import streamlit as st
import pandas as pd

# Load Recipe Data
@st.cache
def load_recipes():
    return pd.DataFrame([
        {"Meal Name": "Chicken Shawarma", "Cuisine": "Mediterranean", "Protein": "Chicken", "Veggies": "Cucumber, Tomato", "Prep Time": 30, "Cook Type": "Stove Top", "Ingredients": "1 lb Chicken thighs, 2 tbsp Shawarma spices, 2 tbsp Olive oil, 1 whole Cucumber, 1 whole Tomato", "Instructions": "link1"},
        {"Meal Name": "Beef Stir-Fry", "Cuisine": "Asian", "Protein": "Beef", "Veggies": "Broccoli, Bell Pepper", "Prep Time": 25, "Cook Type": "Stove Top", "Ingredients": "1 lb Beef, 2 cups Broccoli florets, 1 whole Bell pepper, 3 tbsp Soy sauce, 1 tbsp Sesame oil", "Instructions": "link2"},
        {"Meal Name": "Vegetarian Enchiladas", "Cuisine": "Mexican", "Protein": "Beans", "Veggies": "Bell Pepper, Tomato", "Prep Time": 40, "Cook Type": "Oven", "Ingredients": "2 cups Black beans, 1 whole Bell pepper, 1 whole Onion, 1 whole Tomato, 1 cup Enchilada sauce, 6 Gluten-free tortillas", "Instructions": "link3"},
        {"Meal Name": "Greek Salad with Chicken", "Cuisine": "Mediterranean", "Protein": "Chicken", "Veggies": "Cucumber, Tomato", "Prep Time": 20, "Cook Type": "No Cook", "Ingredients": "2 Chicken breasts, 1 whole Cucumber, 2 whole Tomatoes, 1 Bell pepper, 1/4 cup Feta cheese (optional), 2 tbsp Olive oil", "Instructions": "link4"},
        {"Meal Name": "Pad Thai", "Cuisine": "Asian", "Protein": "Tofu", "Veggies": "Carrot, Bean Sprouts", "Prep Time": 35, "Cook Type": "Stove Top", "Ingredients": "8 oz Rice noodles, 1 whole Carrot, 1 cup Bean sprouts, 2 tbsp Tamarind sauce, 1 tbsp Sesame oil", "Instructions": "link5"},
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

# Function to Filter by Prep Time Interval
def filter_by_prep_time(data, interval):
    if interval == "< 30 mins":
        return data[data["Prep Time"] < 30]
    elif interval == "30-45 mins":
        return data[(data["Prep Time"] >= 30) & (data["Prep Time"] <= 45)]
    elif interval == "> 45 mins":
        return data[data["Prep Time"] > 45]
    else:  # "Any"
        return data

# Apply Filters
filtered_recipes = recipes[
    ((recipes["Cuisine"] == cuisine_filter) | (cuisine_filter == "Any")) &
    ((recipes["Protein"] == protein_filter) | (protein_filter == "Any")) &
    ((recipes["Cook Type"] == cook_type_filter) | (cook_type_filter == "Any"))
]
filtered_recipes = filter_by_prep_time(filtered_recipes, prep_time_filter)

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
    ingredient_list = selected_recipes["Ingredients"].str.split(", ").explode()
    grocery_list = ingredient_list.value_counts().reset_index()
    grocery_list.columns = ["Ingredient", "Quantity"]
    st.write("### Grocery List")
    st.table(grocery_list)