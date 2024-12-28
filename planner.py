import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import openai

# Google Sheets and OpenAI configurations
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

def connect_to_gsheet():
    service_account_info = st.secrets["google_service_account"]
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open("Weekly_Dinner_Planner")  # Replace with your Google Sheet name
    return sheet

def load_recipes(sheet):
    worksheet = sheet.worksheet("Recipe Database")
    return pd.DataFrame(worksheet.get_all_records())

def load_ingredients_database(sheet):
    worksheet = sheet.worksheet("Ingredients Database")
    return pd.DataFrame(worksheet.get_all_records())

def scale_ingredients(ingredients_db, meal_name, servings, original_servings):
    ingredients = ingredients_db[ingredients_db["Meal Name"] == meal_name]
    if original_servings == 0:
        return ingredients
    ingredients["Quantity"] = ingredients["Quantity"] * (servings / original_servings)
    return ingredients

# Recipe Planner
def recipe_planner(recipes):
    st.title("Weekly Recipe Planner")
    st.markdown("""
        ### How to Use
        1. Use the filters in the sidebar to narrow down recipes.
        2. Assign recipes to days of the week.
        3. Click **Generate Grocery List** to create a shopping list.
    """)

    # Initialize session state for weekly plan
    if "weekly_plan" not in st.session_state:
        st.session_state["weekly_plan"] = {day: "None" for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}

    # Filter Recipes
    cuisine_filter = st.sidebar.selectbox("Cuisine", ["Any"] + recipes["Cuisine"].unique().tolist())
    protein_filter = st.sidebar.selectbox("Protein", ["Any"] + recipes["Protein"].unique().tolist())
    cook_type_filter = st.sidebar.selectbox("Cook Type", ["Any"] + recipes["Cook Type"].unique().tolist())

    filtered_recipes = recipes[
        ((recipes["Cuisine"] == cuisine_filter) | (cuisine_filter == "Any")) &
        ((recipes["Protein"] == protein_filter) | (protein_filter == "Any")) &
        ((recipes["Cook Type"] == cook_type_filter) | (cook_type_filter == "Any"))
    ]

    # Assign Recipes to Days
    st.write("## Assign Recipes to Days")
    columns = st.columns(7)
    for i, day in enumerate(st.session_state["weekly_plan"].keys()):
        with columns[i]:
            st.write(f"### {day}")
            options = ["None"] + filtered_recipes["Meal Name"].tolist()
            st.session_state["weekly_plan"][day] = st.selectbox(
                f"Select recipe for {day}",
                options=options,
                index=options.index(st.session_state["weekly_plan"].get(day, "None"))
            )

    # Display Weekly Plan
    st.write("### Weekly Plan")
    st.table(pd.DataFrame(list(st.session_state["weekly_plan"].items()), columns=["Day", "Meal"]))

# Add Recipes
def add_recipes(sheet):
    st.title("Add a New Recipe")
    st.markdown("""
        ### How to Add
        1. Fill out recipe details.
        2. Add ingredients with quantities and units.
        3. Click **Add Recipe** to save it.
    """)

    with st.form("add_recipe_form"):
        meal_name = st.text_input("Meal Name")
        cuisine = st.selectbox("Cuisine", ["Mediterranean", "Asian", "Mexican", "Indian", "Italian", "Other"])
        protein = st.selectbox("Protein", ["Chicken", "Beef", "Beans", "Tofu", "Fish", "Other"])
        prep_time = st.number_input("Prep Time (minutes)", min_value=1, max_value=120, step=1)
        cook_type = st.selectbox("Cook Type", ["Stove Top", "Oven", "No Cook", "Grill", "Other"])
        instructions = st.text_input("Instructions (link or description)")
        num_ingredients = st.number_input("Number of Ingredients", min_value=1, max_value=20, value=1, step=1)

        ingredients = []
        for i in range(num_ingredients):
            col1, col2, col3 = st.columns(3)
            ingredient = col1.text_input(f"Ingredient {i+1}", key=f"ingredient_{i}")
            quantity = col2.number_input(f"Quantity {i+1}", min_value=0.0, step=0.1, key=f"quantity_{i}")
            unit = col3.text_input(f"Unit {i+1}", key=f"unit_{i}")
            ingredients.append({"Ingredient": ingredient, "Quantity": quantity, "Unit": unit})

        submitted = st.form_submit_button("Add Recipe")

    if submitted:
        if not meal_name or not ingredients[0]["Ingredient"]:
            st.error("Please fill in all required fields.")
        else:
            worksheet = sheet.worksheet("Recipe Database")
            worksheet.append_row([meal_name, cuisine, protein, prep_time, cook_type, instructions])

            ingredients_sheet = sheet.worksheet("Ingredients Database")
            for ingredient in ingredients:
                ingredients_sheet.append_row([meal_name, ingredient["Ingredient"], ingredient["Quantity"], ingredient["Unit"]])

            st.success(f"Recipe '{meal_name}' added successfully!")

# Browse Recipes
def browse_recipes(recipes, ingredients_db):
    st.title("Browse Recipes")
    recipe_name = st.selectbox("Select a Recipe", recipes["Meal Name"].unique())
    selected_recipe = recipes[recipes["Meal Name"] == recipe_name].iloc[0]
    st.subheader(f"Recipe: {selected_recipe['Meal Name']}")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**Cuisine**: {selected_recipe['Cuisine']}")
        st.markdown(f"**Protein**: {selected_recipe['Protein']}")
        st.markdown(f"**Cook Type**: {selected_recipe['Cook Type']}")
        st.markdown(f"**Prep Time**: {selected_recipe['Prep Time']} minutes")
        st.markdown(f"**Instructions**: {selected_recipe['Instructions']}")

    with col2:
        st.image("https://via.placeholder.com/150", caption="Recipe Image (Placeholder)")

    servings = st.number_input("Number of Servings", min_value=1, value=4, step=1)
    original_servings = 4
    scaled_ingredients = scale_ingredients(ingredients_db, recipe_name, servings, original_servings)
    st.write("### Ingredients")
    st.table(scaled_ingredients[["Ingredient", "Quantity", "Unit"]])

# Chat Assistant
def chat_interface_with_streamlit_chat(recipes):
    st.title("Recipe Assistant")

    openai.api_key = st.secrets["general"]["openai_api_key"]

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.chat_input("What would you like to know?"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        prompt = f"You are a recipe assistant. Here is a user's question:\n\n{user_input}"
        response = openai.Completion.create(
            model="gpt-3.5-turbo",
            prompt=prompt,
            max_tokens=200,
            temperature=0.7
        )
        assistant_reply = response.choices[0].text.strip()

        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
        with st.chat_message("assistant"):
            st.markdown(assistant_reply)

# Main App
sheet = connect_to_gsheet()
recipes = load_recipes(sheet)
ingredients_db = load_ingredients_database(sheet)

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Recipe Planner", "Add Recipes", "Browse Recipes", "Chat Assistant"])

if page == "Recipe Planner":
    recipe_planner(recipes)
elif page == "Add Recipes":
    add_recipes(sheet)
elif page == "Browse Recipes":
    browse_recipes(recipes, ingredients_db)
elif page == "Chat Assistant":
    chat_interface_with_streamlit_chat(recipes)