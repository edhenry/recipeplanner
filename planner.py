import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from collections import defaultdict

# Custom CSS to disable word wrapping in Streamlit tables
st.markdown(
    """
    <style>
    table {
        word-wrap: normal;
        white-space: nowrap;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Correct scopes for Google Sheets and Drive API
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Google Sheets connection
def connect_to_gsheet():
    service_account_info = st.secrets["google_service_account"]
    creds = Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open("Weekly_Dinner_Planner")  # Replace with your Google Sheet name
    return sheet

# Load recipes from Google Sheet
def load_recipes(sheet):
    worksheet = sheet.worksheet("Recipe Database")
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# Load Ingredients Database from Google Sheet
def load_ingredients_database(sheet):
    worksheet = sheet.worksheet("Ingredients Database")
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
        recipe["Instructions"]
    ])

# Filter recipes based on user inputs
def filter_recipes(recipes, cuisine_filter, protein_filter, cook_type_filter, prep_time_filter):
    filtered_recipes = recipes[
        ((recipes["Cuisine"] == cuisine_filter) | (cuisine_filter == "Any")) &
        ((recipes["Protein"] == protein_filter) | (protein_filter == "Any")) &
        ((recipes["Cook Type"] == cook_type_filter) | (cook_type_filter == "Any"))
    ]

    if prep_time_filter == "< 30 mins":
        filtered_recipes = filtered_recipes[filtered_recipes["Prep Time"] < 30]
    elif prep_time_filter == "30-45 mins":
        filtered_recipes = filtered_recipes[(filtered_recipes["Prep Time"] >= 30) & (filtered_recipes["Prep Time"] <= 45)]
    elif prep_time_filter == "> 45 mins":
        filtered_recipes = filtered_recipes[filtered_recipes["Prep Time"] > 45]

    return filtered_recipes

# Generate grocery list using Ingredients Database
def generate_grocery_list_from_db(ingredients_db, selected_recipes):
    selected_ingredients = ingredients_db[ingredients_db["Meal Name"].isin(selected_recipes["Meal Name"])]
    grocery_list = selected_ingredients.groupby(["Ingredient", "Unit"], as_index=False).agg({"Quantity": "sum"})
    return grocery_list

# Scale ingredients based on servings
def scale_ingredients(ingredients_db, meal_name, servings, original_servings):
    ingredients = ingredients_db[ingredients_db["Meal Name"] == meal_name]
    if original_servings == 0:
        return ingredients
    ingredients["Quantity"] = ingredients["Quantity"] * (servings / original_servings)
    return ingredients

# Assign recipes to days with persistent selections
def assign_recipes_to_days(filtered_recipes):
    st.write("## Assign Recipes to Days")
    if "weekly_plan" not in st.session_state:
        st.session_state["weekly_plan"] = {day: "None" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}

    for day in st.session_state["weekly_plan"]:
        current_selection = st.session_state["weekly_plan"][day]
        dropdown_options = ["None"] + filtered_recipes["Meal Name"].tolist()
        if current_selection not in dropdown_options and current_selection != "None":
            dropdown_options.append(current_selection)
        selected_recipe = st.selectbox(
            f"Select a recipe for {day}",
            options=dropdown_options,
            index=dropdown_options.index(current_selection),
            key=f"{day}_recipe"
        )
        st.session_state["weekly_plan"][day] = selected_recipe

    st.write("### Your Weekly Plan")
    st.table(pd.DataFrame(list(st.session_state["weekly_plan"].items()), columns=["Day", "Meal"]).reset_index(drop=True))

# Browse Recipes Page
def browse_recipes(recipes, ingredients_db):
    st.title("Browse Recipes")
    st.markdown(
        """
        ### Browse All Recipes
        1. Select a recipe from the dropdown to view its details.
        2. Adjust the number of servings to scale the ingredient quantities.
        """
    )
    recipe_name = st.selectbox("Select a Recipe", recipes["Meal Name"].unique())
    selected_recipe = recipes[recipes["Meal Name"] == recipe_name].iloc[0]

    st.subheader(f"Recipe: {selected_recipe['Meal Name']}")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(
            f"""
            **Cuisine**: {selected_recipe['Cuisine']}  
            **Cook Type**: {selected_recipe['Cook Type']}  
            **Prep Time**: {selected_recipe['Prep Time']} minutes  
            """
        )
        st.write("### Instructions")
        st.markdown(selected_recipe["Instructions"])
    with col2:
        st.image(
            "https://via.placeholder.com/150",
            caption="Recipe Image (Placeholder)",
            use_container_width=True
        )

    st.write("### Ingredients")
    servings = st.number_input("Number of Servings", min_value=1, value=4, step=1, help="Adjust servings to scale ingredients.")
    original_servings = 4  # Default serving size; can adjust if you track it in the Recipe Database
    scaled_ingredients = scale_ingredients(ingredients_db, recipe_name, servings, original_servings)
    st.table(scaled_ingredients[["Ingredient", "Quantity", "Unit"]].reset_index(drop=True))

# Main app
sheet = connect_to_gsheet()
st.sidebar.title("Navigation")
st.sidebar.info(
    """
    **Welcome to the Weekly Dinner Planner!**

    - **Recipe Planner**: Plan your weekly meals and generate a grocery list.
    - **Add Recipes**: Add new recipes with ingredients to your database.
    - **Browse Recipes**: View and scale recipes with ingredients.
    """
)
page = st.sidebar.radio("Go to", ["Recipe Planner", "Add Recipes", "Browse Recipes"])

if page == "Recipe Planner":
    st.title("Weekly Recipe Planner")
    st.markdown(
        """
        ### How to Use the Recipe Planner
        1. Use the filters in the sidebar to narrow down recipes.
        2. Assign recipes to each day of the week.
        3. Click **"Generate Grocery List"** to create your shopping list.
        """
    )
    recipes = load_recipes(sheet)
    ingredients_db = load_ingredients_database(sheet)
    cuisine_filter = st.sidebar.selectbox("Cuisine", ["Any"] + recipes["Cuisine"].unique().tolist())
    protein_filter = st.sidebar.selectbox("Protein", ["Any"] + recipes["Protein"].unique().tolist())
    cook_type_filter = st.sidebar.selectbox("Cook Type", ["Any"] + recipes["Cook Type"].unique().tolist())
    prep_time_filter = st.sidebar.selectbox("Prep Time", ["Any", "< 30 mins", "30-45 mins", "> 45 mins"])
    filtered_recipes = filter_recipes(recipes, cuisine_filter, protein_filter, cook_type_filter, prep_time_filter)

    st.write("## Filtered Recipes")
    if filtered_recipes.empty:
        st.write("No recipes match your criteria.")
    else:
        st.table(filtered_recipes.reset_index(drop=True))
    assign_recipes_to_days(filtered_recipes)

    if st.button("Generate Grocery List"):
        selected_recipes = recipes[recipes["Meal Name"].isin(st.session_state["weekly_plan"].values())]
        grocery_list = generate_grocery_list_from_db(ingredients_db, selected_recipes)
        st.write("### Grocery List")
        st.table(grocery_list.reset_index(drop=True))

elif page == "Add Recipes":
    st.title("Add a New Recipe")
    st.markdown(
        """
        ### How to Add a Recipe
        1. Fill out recipe details.
        2. Add ingredients with quantities and units.
        3. Click **"Add Recipe"** to save it.
        """
    )
    with st.form("add_recipe_form"):
        meal_name = st.text_input("Meal Name")
        cuisine = st.selectbox("Cuisine", ["Mediterranean", "Asian", "Mexican", "Indian", "Italian", "Other"])
        protein = st.selectbox("Protein", ["Chicken", "Beef", "Beans", "Tofu", "Fish", "Other"])
        veggies = st.text_input("Veggies (comma-separated)")
        prep_time = st.number_input("Prep Time (minutes)", min_value=1, max_value=120, step=1)
        cook_type = st.selectbox("Cook Type", ["Stove Top", "Oven", "No Cook", "Grill", "Other"])
        instructions = st.text_input("Instructions (link or description)")
        num_ingredients = st.number_input("Number of Ingredients", min_value=1, max_value=20, value=1, step=1)
        ingredient_data = []
        for i in range(num_ingredients):
            col1, col2, col3 = st.columns(3)
            ingredient = col1.text_input(f"Ingredient {i + 1}", key=f"ingredient_{i}")
            quantity = col2.number_input(f"Quantity {i + 1}", min_value=0.0, step=0.1, key=f"quantity_{i}")
            unit = col3.text_input(f"Unit {i + 1}", key=f"unit_{i}")
            ingredient_data.append({"Ingredient": ingredient, "Quantity": quantity, "Unit": unit})
        submitted = st.form_submit_button("Add Recipe")

    if submitted:
        if not meal_name:
            st.error("Meal Name is required.")
        elif not any(ingredient["Ingredient"] for ingredient in ingredient_data):
            st.error("At least one ingredient is required.")
        else:
            recipe = {
                "Meal Name": meal_name,
                "Cuisine": cuisine,
                "Protein": protein,
                "Veggies": veggies,
                "Prep Time": prep_time,
                "Cook Type": cook_type,
                "Instructions": instructions
            }
            add_recipe_to_gsheet(sheet, recipe)
            ingredients_sheet = sheet.worksheet("Ingredients Database")
            for ingredient in ingredient_data:
                if ingredient["Ingredient"]:
                    ingredients_sheet.append_row([meal_name, ingredient["Ingredient"], ingredient["Quantity"], ingredient["Unit"]])
            st.success(f"Recipe '{meal_name}' added successfully!")

elif page == "Browse Recipes":
    recipes = load_recipes(sheet)
    ingredients_db = load_ingredients_database(sheet)
    browse_recipes(recipes, ingredients_db)