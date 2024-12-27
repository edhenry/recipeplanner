import streamlit as st
import pandas as pd
from collections import defaultdict

# Load Recipe Data
@st.cache_data
def load_recipes():
    return pd.DataFrame([
        {"Meal Name": "Chicken Shawarma", "Cuisine": "Mediterranean", "Protein": "Chicken", "Veggies": "Cucumber, Tomato", "Prep Time": 30, "Cook Type": "Stove Top", "Ingredients": [
            {"quantity": 1, "unit": "lb", "item": "chicken thighs"},
            {"quantity": 2, "unit": "tbsp", "item": "shawarma spices"},
            {"quantity": 2, "unit": "tbsp", "item": "olive oil"},
            {"quantity": 1, "unit": "whole", "item": "cucumber"},
            {"quantity": 1, "unit": "whole", "item": "tomato"}
        ], "Instructions": "link1"},
        {"Meal Name": "Beef Stir-Fry", "Cuisine": "Asian", "Protein": "Beef", "Veggies": "Broccoli, Bell Pepper", "Prep Time": 25, "Cook Type": "Stove Top", "Ingredients": [
            {"quantity": 1, "unit": "lb", "item": "beef"},
            {"quantity": 2, "unit": "cups", "item": "broccoli florets"},
            {"quantity": 1, "unit": "whole", "item": "bell pepper"},
            {"quantity": 3, "unit": "tbsp", "item": "soy sauce"},
            {"quantity": 1, "unit": "tbsp", "item": "sesame oil"}
        ], "Instructions": "link2"},
    ])

# Sidebar Filters
st.sidebar.header("Filter Recipes")
recipes = load_recipes()

# Dropdown for Cuisine, Protein, Cook Type
cuisine_filter = st.sidebar.selectbox("Cuisine", ["Any"] + recipes["Cuisine"].unique().tolist())
protein_filter = st.sidebar.selectbox("Protein", ["Any"] + recipes["Protein"].unique().tolist())
cook_type_filter = st.sidebar.selectbox("Cook Type", ["Any"] + recipes["Cook Type"].unique().tolist())

# Dropdown for Prep Time Intervals
prep_time_intervals = ["Any", "< 30 mins", "30-45 mins", "> 45 mins"]
prep_time_filter = st.sidebar.selectbox("Prep Time", prep_time_intervals)

# Filter Recipes
filtered_recipes = recipes[
    ((recipes["Cuisine"] == cuisine_filter) | (cuisine_filter == "Any")) &
    ((recipes["Protein"] == protein_filter) | (protein_filter == "Any")) &
    ((recipes["Cook Type"] == cook_type_filter) | (cook_type_filter == "Any"))
]

st.write("## Filtered Recipes")
if filtered_recipes.empty:
    st.write("No recipes match your criteria.")
else:
    st.dataframe(filtered_recipes)

# Assign Recipes to Days
st.write("## Assign Recipes to Days")
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekly_plan = {}

for day in days:
    selected_recipe = st.selectbox(f"Select a recipe for {day}", ["None"] + filtered_recipes["Meal Name"].tolist())
    weekly_plan[day] = selected_recipe

# Display Final Weekly Plan
st.write("### Your Weekly Plan")
selected_recipes = recipes[recipes["Meal Name"].isin(weekly_plan.values())]
st.table(selected_recipes[["Meal Name", "Cuisine", "Protein", "Cook Type", "Prep Time", "Instructions"]])

# Generate Grocery List
if st.button("Generate Grocery List"):
    grocery_list = defaultdict(lambda: defaultdict(float))

    # Aggregate Ingredients
    for ingredients in selected_recipes["Ingredients"]:
        for ingredient in ingredients:
            item = ingredient["item"]
            unit = ingredient["unit"]
            grocery_list[item][unit] += ingredient["quantity"]

    # Convert to DataFrame
    grocery_list_df = pd.DataFrame([
        {"Ingredient": item, "Unit": unit, "Quantity": qty}
        for item, units in grocery_list.items()
        for unit, qty in units.items()
    ])

    st.write("### Grocery List")
    st.table(grocery_list_df)