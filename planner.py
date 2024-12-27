import streamlit as st
import pandas as pd

# Load Recipe Data
@st.cache
def load_recipes():
    return pd.DataFrame({
        "Meal Name": ["Chicken Shawarma", "Beef Stir-Fry", "Vegetarian Enchiladas", "Greek Salad", "Pad Thai"],
        "Cuisine": ["Mediterranean", "Asian", "Mexican", "Mediterranean", "Asian"],
        "Protein": ["Chicken", "Beef", "Beans", "Chicken", "Tofu"],
        "Prep Time": [30, 25, 40, 20, 35],
        "Cook Type": ["Stove Top", "Stove Top", "Oven", "Stove Top", "Stove Top"],
        "Instructions": ["link1", "link2", "link3", "link4", "link5"]
    })

# Sidebar Filters
st.sidebar.header("Filter Recipes")
recipes = load_recipes()
cuisine_filter = st.sidebar.selectbox("Cuisine", ["Any"] + recipes["Cuisine"].unique().tolist())
protein_filter = st.sidebar.selectbox("Protein", ["Any"] + recipes["Protein"].unique().tolist())
cook_type_filter = st.sidebar.selectbox("Cook Type", ["Any"] + recipes["Cook Type"].unique().tolist())
max_prep_time = st.sidebar.slider("Max Prep Time (minutes)", 0, 60, 30)

# Filter Recipes
filtered_recipes = recipes[
    ((recipes["Cuisine"] == cuisine_filter) | (cuisine_filter == "Any")) &
    ((recipes["Protein"] == protein_filter) | (protein_filter == "Any")) &
    ((recipes["Cook Type"] == cook_type_filter) | (cook_type_filter == "Any")) &
    (recipes["Prep Time"] <= max_prep_time)
]

st.write("## Filtered Recipes")
if filtered_recipes.empty:
    st.write("No recipes match your criteria.")
else:
    st.dataframe(filtered_recipes)

# Multi-Select for Drag-and-Drop Feel
st.write("## Assign Recipes to Days")
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekly_plan = {}

# Create Multi-Select Dropdowns for Each Day
for day in days:
    selected_recipe = st.selectbox(f"{day}", ["None"] + filtered_recipes["Meal Name"].tolist())
    weekly_plan[day] = selected_recipe

# Display Final Weekly Plan
st.write("### Your Weekly Plan")
st.table(pd.DataFrame(list(weekly_plan.items()), columns=["Day", "Meal"]))