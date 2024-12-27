import streamlit as st
import pandas as pd
import json
from google.oauth2.service_account import Credentials
import gspread
from collections import defaultdict

# Google Sheets connection
def connect_to_gsheet():
    service_account_info = st.secrets["google_service_account"]
    creds = Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    sheet = client.open("Weekly_Dinner_Plannerg")  # Replace with your Google Sheet name
    return sheet

# Load recipes from Google Sheet
def load_recipes(sheet):
    worksheet = sheet.worksheet("Recipe Database")  # Replace with the correct sheet name
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# Add a new recipe to Google Sheet
def add_recipe_to_gsheet(sheet, recipe):
    worksheet = sheet.worksheet("Recipe Database")
    worksheet.append_row([
        recipe["Meal Name"],
        recipe["Cuisine"],
        recipe["Protein"],
        recipe["Veggies"],
        recipe["Prep Time"],
        recipe["Cook Type"],
        recipe["Ingredients"],
        recipe["Instructions"]
    ])

# Filter recipes based on user inputs
def filter_recipes(recipes, cuisine_filter, protein_filter, cook_type_filter, prep_time_filter):
    # Filter by cuisine, protein, and cook type
    filtered_recipes = recipes[
        ((recipes["Cuisine"] == cuisine_filter) | (cuisine_filter == "Any")) &
        ((recipes["Protein"] == protein_filter) | (protein_filter == "Any")) &
        ((recipes["Cook Type"] == cook_type_filter) | (cook_type_filter == "Any"))
    ]

    # Filter by prep time range
    if prep_time_filter == "< 30 mins":
        filtered_recipes = filtered_recipes[filtered_recipes["Prep Time"] < 30]
    elif prep_time_filter == "30-45 mins":
        filtered_recipes = filtered_recipes[(filtered_recipes["Prep Time"] >= 30) & (filtered_recipes["Prep Time"] <= 45)]
    elif prep_time_filter == "> 45 mins":
        filtered_recipes = filtered_recipes[filtered_recipes["Prep Time"] > 45]

    return filtered_recipes

# Generate grocery list
def generate_grocery_list(selected_recipes):
    grocery_list = defaultdict(lambda: defaultdict(float))

    # Parse ingredients and aggregate by item
    for ingredients in selected_recipes["Ingredients"]:
        for ingredient in ingredients.split(", "):
            parts = ingredient.split(" ", 2)
            if len(parts) == 3:
                quantity, unit, item = parts
                try:
                    quantity = float(quantity)
                except ValueError:
                    quantity = 0
                grocery_list[item][unit] += quantity

    # Convert to DataFrame for display
    grocery_list_df = pd.DataFrame([
        {"Ingredient": item, "Unit": unit, "Quantity": qty}
        for item, units in grocery_list.items()
        for unit, qty in units.items()
    ])
    return grocery_list_df

# Main app
sheet = connect_to_gsheet()

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Recipe Planner", "Add Recipes"])

if page == "Recipe Planner":
    st.title("Weekly Recipe Planner")

    # Load recipes
    recipes = load_recipes(sheet)

    # Sidebar Filters
    st.sidebar.header("Filter Recipes")
    cuisine_filter = st.sidebar.selectbox("Cuisine", ["Any"] + recipes["Cuisine"].unique().tolist())
    protein_filter = st.sidebar.selectbox("Protein", ["Any"] + recipes["Protein"].unique().tolist())
    cook_type_filter = st.sidebar.selectbox("Cook Type", ["Any"] + recipes["Cook Type"].unique().tolist())
    prep_time_intervals = ["Any", "< 30 mins", "30-45 mins", "> 45 mins"]
    prep_time_filter = st.sidebar.selectbox("Prep Time", prep_time_intervals)

    # Filter recipes
    filtered_recipes = filter_recipes(recipes, cuisine_filter, protein_filter, cook_type_filter, prep_time_filter)

    st.write("## Filtered Recipes")
    if filtered_recipes.empty:
        st.write("No recipes match your criteria.")
    else:
        st.dataframe(filtered_recipes)

    # Assign recipes to days
    st.write("## Assign Recipes to Days")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekly_plan = {}

    for day in days:
        selected_recipe = st.selectbox(f"Select a recipe for {day}", ["None"] + filtered_recipes["Meal Name"].tolist())
        weekly_plan[day] = selected_recipe

    # Display weekly plan
    st.write("### Your Weekly Plan")
    selected_recipes = recipes[recipes["Meal Name"].isin(weekly_plan.values())]
    st.table(selected_recipes[["Meal Name", "Cuisine", "Protein", "Cook Type", "Prep Time", "Instructions"]])

    # Generate grocery list
    if st.button("Generate Grocery List"):
        grocery_list = generate_grocery_list(selected_recipes)
        st.write("### Grocery List")
        st.table(grocery_list)

elif page == "Add Recipes":
    st.title("Add a New Recipe")

    # Recipe Input Form
    with st.form("add_recipe_form"):
        meal_name = st.text_input("Meal Name")
        cuisine = st.selectbox("Cuisine", ["Mediterranean", "Asian", "Mexican", "Indian", "Italian", "Other"])
        protein = st.selectbox("Protein", ["Chicken", "Beef", "Beans", "Tofu", "Fish", "Other"])
        veggies = st.text_input("Veggies (comma-separated)")
        prep_time = st.number_input("Prep Time (minutes)", min_value=1, max_value=120, step=1)
        cook_type = st.selectbox("Cook Type", ["Stove Top", "Oven", "No Cook", "Grill", "Other"])
        ingredients = st.text_area("Ingredients (quantity, unit, item - one per line)")
        instructions = st.text_input("Instructions (link or description)")

        # Submit button
        submitted = st.form_submit_button("Add Recipe")

    if submitted:
        # Parse ingredients into a single string
        ingredients_list = ingredients.split("\n")
        recipe = {
            "Meal Name": meal_name,
            "Cuisine": cuisine,
            "Protein": protein,
            "Veggies": veggies,
            "Prep Time": prep_time,
            "Cook Type": cook_type,
            "Ingredients": ", ".join(ingredients_list),
            "Instructions": instructions,
        }

        # Save recipe
        add_recipe_to_gsheet(sheet, recipe)
        st.success(f"Recipe '{meal_name}' added successfully!")