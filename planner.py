import streamlit as st
import pandas as pd

# Load Recipe Data
@st.cache
def load_recipes():
    return pd.DataFrame([
        {"Meal Name": "Chicken Shawarma", "Cuisine": "Mediterranean", "Protein": "Chicken", "Veggies": "Cucumber, Tomato", "Prep Time": 30, "Cook Type": "Stove Top", "Instructions": "link1"},
        {"Meal Name": "Beef Stir-Fry", "Cuisine": "Asian", "Protein": "Beef", "Veggies": "Broccoli, Bell Pepper", "Prep Time": 25, "Cook Type": "Stove Top", "Instructions": "link2"},
        {"Meal Name": "Vegetarian Enchiladas", "Cuisine": "Mexican", "Protein": "Beans", "Veggies": "Bell Pepper, Tomato", "Prep Time": 40, "Cook Type": "Oven", "Instructions": "link3"},
        {"Meal Name": "Greek Salad with Chicken", "Cuisine": "Mediterranean", "Protein": "Chicken", "Veggies": "Cucumber, Tomato", "Prep Time": 20, "Cook Type": "No Cook", "Instructions": "link4"},
        {"Meal Name": "Pad Thai", "Cuisine": "Asian", "Protein": "Tofu", "Veggies": "Carrot, Bean Sprouts", "Prep Time": 35, "Cook Type": "Stove Top", "Instructions": "link5"},
        {"Meal Name": "Spaghetti Bolognese", "Cuisine": "Italian", "Protein": "Beef", "Veggies": "Carrot, Garlic", "Prep Time": 30, "Cook Type": "Stove Top", "Instructions": "link6"},
        {"Meal Name": "Stuffed Bell Peppers", "Cuisine": "Mediterranean", "Protein": "Beef", "Veggies": "Bell Pepper, Tomato", "Prep Time": 45, "Cook Type": "Oven", "Instructions": "link7"},
        {"Meal Name": "Taco Salad", "Cuisine": "Mexican", "Protein": "Chicken", "Veggies": "Lettuce, Tomato, Bell Pepper", "Prep Time": 20, "Cook Type": "No Cook", "Instructions": "link8"},
        {"Meal Name": "Chickpea Curry", "Cuisine": "Indian", "Protein": "Chickpeas", "Veggies": "Spinach, Tomato", "Prep Time": 30, "Cook Type": "Stove Top", "Instructions": "link9"},
        {"Meal Name": "Mediterranean Quinoa Salad", "Cuisine": "Mediterranean", "Protein": "Beans", "Veggies": "Cucumber, Tomato, Bell Pepper", "Prep Time": 25, "Cook Type": "No Cook", "Instructions": "link10"},
    ])

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

# Assign Recipes to Days
st.write("## Assign Recipes to Days")
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekly_plan = {}

for day in days:
    selected_recipe = st.selectbox(f"Select a recipe for {day}", ["None"] + filtered_recipes["Meal Name"].tolist())
    weekly_plan[day] = selected_recipe

# Display Final Weekly Plan
st.write("### Your Weekly Plan")
st.table(pd.DataFrame(list(weekly_plan.items()), columns=["Day", "Meal"]))