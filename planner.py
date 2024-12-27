import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from collections import defaultdict

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
        scopes=SCOPES  # Use both Sheets and Drive APIs
    )
    client = gspread.authorize(creds)
    sheet = client.open("Weekly_Dinner_Planner")  # Replace with the exact name of your Google Sheet
    return sheet

# Load recipes from Google Sheet
def load_recipes(sheet):
    worksheet = sheet.worksheet("Recipe Database")  # Replace with the correct sheet name
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# Load Ingredients Database from Google Sheet
def load_ingredients_database(sheet):
    worksheet = sheet.worksheet("Ingredients Database")  # Replace with the correct sheet name
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
    # Filter ingredients for selected recipes
    selected_ingredients = ingredients_db[ingredients_db["Meal Name"].isin(selected_recipes["Meal Name"])]

    # Aggregate ingredients by Ingredient and Unit
    grocery_list = selected_ingredients.groupby(["Ingredient", "Unit"], as_index=False).agg({"Quantity": "sum"})

    return grocery_list

# Assign recipes to days with persistent selections
def assign_recipes_to_days(filtered_recipes):
    st.write("## Assign Recipes to Days")
    
    # Initialize session state for weekly plan
    if "weekly_plan" not in st.session_state:
        st.session_state["weekly_plan"] = {day: "None" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}

    # Dropdowns for each day
    for day in st.session_state["weekly_plan"]:
        # Get the current selection for this day
        current_selection = st.session_state["weekly_plan"][day]

        # Include the current selection in the options even if it doesn't match the filters
        dropdown_options = ["None"] + filtered_recipes["Meal Name"].tolist()
        if current_selection not in dropdown_options and current_selection != "None":
            dropdown_options.append(current_selection)  # Add the current selection to the options

        # Create the dropdown
        try:
            selected_recipe = st.selectbox(
                f"Select a recipe for {day}",
                options=dropdown_options,
                index=dropdown_options.index(current_selection),  # Ensure the current selection remains selected
                key=f"{day}_recipe"
            )
        except ValueError:
            # Fallback to "None" if the selection somehow breaks
            selected_recipe = "None"
        
        # Update the session state with the new selection
        st.session_state["weekly_plan"][day] = selected_recipe

    # Display the weekly plan
    st.write("### Your Weekly Plan")
    st.table(pd.DataFrame(list(st.session_state["weekly_plan"].items()), columns=["Day", "Meal"]))

# Main app
sheet = connect_to_gsheet()

st.sidebar.title("Navigation")
st.sidebar.info(
    """
    **Welcome to the Weekly Dinner Planner!**

    Use the options below to navigate:
    - **Recipe Planner**: Plan your weekly meals and generate a grocery list.
    - **Add Recipes**: Add new recipes with ingredients to your database.
    """
)
page = st.sidebar.radio("Go to", ["Recipe Planner", "Add Recipes"])

if page == "Recipe Planner":
    st.title("Weekly Recipe Planner")
    st.markdown(
        """
        ### How to Use the Recipe Planner
        1. Use the filters in the sidebar to narrow down recipes by cuisine, protein, cook type, or prep time.
        2. Assign recipes to each day of the week using the dropdowns below.
        3. Once you've assigned meals, click **"Generate Grocery List"** to create a shopping list for the week.
        """
    )

    # Load recipes and ingredients database
    recipes = load_recipes(sheet)
    ingredients_db = load_ingredients_database(sheet)

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
    assign_recipes_to_days(filtered_recipes)

    # Generate grocery list
    if st.button("Generate Grocery List"):
        selected_recipes = recipes[recipes["Meal Name"].isin(st.session_state["weekly_plan"].values())]
        grocery_list = generate_grocery_list_from_db(ingredients_db, selected_recipes)
        st.write("### Grocery List")
        st.info(
            """
            **Tip**:
            - The grocery list is automatically generated based on the ingredients for the recipes you assigned to the weekly plan.
            - Quantities are aggregated across recipes to simplify shopping.
            """
        )
        st.table(grocery_list)

elif page == "Add Recipes":
    st.title("Add a New Recipe")
    st.markdown(
        """
        ### How to Add a New Recipe
        1. Fill out the details for your recipe, including:
           - **Meal Name**: The name of your dish (e.g., Chicken Stir-Fry).
           - **Cuisine**: Select the type of cuisine.
           - **Protein**: Choose the primary protein for the dish.
           - **Veggies**: List any key vegetables in the recipe (comma-separated).
           - **Prep Time**: Enter the approximate preparation time in minutes.
           - **Cook Type**: Select the primary cooking method.
           - **Instructions**: Add a link to the recipe or a brief description of the steps.
        2. Use the **Ingredients Section** to specify the ingredients for your recipe:
           - Enter the ingredient name, quantity, and unit for each ingredient.
           - Adjust the number of ingredients as needed.
        3. Click **"Add Recipe"** to save your recipe to the database.
        """
    )

    # Recipe Input Form
    with st.form("add_recipe_form"):
        meal_name = st.text_input("Meal Name", help="Enter the name of your dish (e.g., Chicken Stir-Fry).")
        cuisine = st.selectbox("Cuisine", ["Mediterranean", "Asian", "Mexican", "Indian", "Italian", "Other"])
        protein = st.selectbox("Protein", ["Chicken", "Beef", "Beans", "Tofu", "Fish", "Other"])
        veggies = st.text_input("Veggies (comma-separated)", help="List key vegetables, separated by commas.")
        prep_time = st.number_input(
            "Prep Time (minutes)", 
            min_value=1, max_value=120, step=1, 
            help="Enter the approximate preparation time for the dish."
        )
        cook_type = st.selectbox(
            "Cook Type", 
            ["Stove Top", "Oven", "No Cook", "Grill", "Other"], 
            help="Select the primary cooking method."
        )
        instructions = st.text_input("Instructions (link or description)", help="Add a link or brief description.")

        st.write("### Ingredients")
        num_ingredients = st.number_input(
            "Number of Ingredients", 
            min_value=1, max_value=20, step=1, value=1, 
            help="Specify the number of ingredients for your recipe."
        )

        ingredient_data = []
        for i in range(num_ingredients):
            col1, col2, col3 = st.columns(3)
            with col1:
                ingredient = st.text_input(f"Ingredient {i + 1}", key=f"ingredient_{i}")
            with col2:
                quantity = st.number_input(f"Quantity {i + 1}", min_value=0.0, step=0.1, key=f"quantity_{i}")
            with col3:
                unit = st.text_input(f"Unit {i + 1}", key=f"unit_{i}")
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
                "Instructions": instructions,
            }
            add_recipe_to_gsheet(sheet, recipe)

            worksheet = sheet.worksheet("Ingredients Database")
            for ingredient in ingredient_data:
                if ingredient["Ingredient"]:
                    worksheet.append_row([
                        meal_name, ingredient["Ingredient"], ingredient["Quantity"], ingredient["Unit"]
                    ])
            st.success(f"Recipe '{meal_name}' and its ingredients were added successfully!")