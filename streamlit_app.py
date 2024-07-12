from openai import OpenAI
import streamlit as st

client = OpenAI(api_key="sk-sea-service-account-QpjdkS5UuD4xgu5RXdzDT3BlbkFJej0KTpg1FTXVjXizosNr")

# Title and description
st.title("💬 AI-Powered No-Waste Chatbot")
st.write(
    "Welcome to the No-Waste Chatbot! This chatbot uses OpenAI's GPT-3.5-turbo model to generate the most waste free options based on your input. "
    "To use this app, please provide some basic information about your event."
)

# Initialize session state
if "state" not in st.session_state:
    st.session_state.state = "start"

if "name" not in st.session_state:
    st.session_state.name = ""
if "event" not in st.session_state:
    st.session_state.event = ""
if "people_amount" not in st.session_state:
    st.session_state.people_amount = ""
if "meal_count" not in st.session_state:
    st.session_state.meal_count = ""
if "responses" not in st.session_state:
    st.session_state.responses = []
if "messages" not in st.session_state:
    st.session_state.messages = []

# Define the dialog tree with polite messages
dialog_tree = {
    "start": {
        "message": "Let's get started with your waste free event. What is your name?",
        "next_state": "get_name"
    },
    "get_name": {
        "message": "Hi {name}! What is your event? (e.g., Birthday, Anniversary, Reunion)",
        "next_state": "get_event"
    },
    "get_event": {
        "message": "Great! How many people are going to attend?",
        "next_state": "get_people_amount"
    },
    "get_people_amount": {
        "message": "Got it. How many meals are going to be served other than appetizers? (e.g., 3, 4, 5)",
        "next_state": "provide_event_plan"
    },
    "provide_event_plan": {
        "message": "Thank you! Based on the information provided, here is your personalized meal plan:\n\n"
                   "Name: {name}\n"
                   "Event: {event}\n"
                   "People amount: {people_amount}\n"
                   "Meals during event: {meal_count}\n\n"
                   "Meal Plan:\n",
        "next_state": None
    }
}

# Function to handle dialog
def handle_dialog(state, user_input=None):
    if state == "start":
        return dialog_tree[state]["message"], dialog_tree[state]["next_state"], True
    elif state == "get_name":
        name = extract_entity(user_input, "name")
        if name:
            st.session_state.name = name
            return dialog_tree[state]["message"].format(name=st.session_state.name), dialog_tree[state]["next_state"], True
        else:
            return "I didn't catch that. Could you please tell me your name?", state, False
    elif state == "get_event":
        event = extract_entity(user_input, "event")
        if event:
            st.session_state.event = event
            return dialog_tree[state]["message"], dialog_tree[state]["next_state"], True
        else:
            return "I didn't catch that. Could you please tell me your event?", state, False
    elif state == "get_people_amount":
        people_amount = extract_entity(user_input, "people_amount")
        print(f"Extracted people_amount: {people_amount}")  # Debugging statement
        if people_amount:
            st.session_state.people_amount = people_amount
            return dialog_tree[state]["message"], dialog_tree[state]["next_state"], True
        else:
            return "I didn't catch that. How many people will attend?", state, False
    elif state == "provide_event_plan":
        meal_count = extract_entity(user_input, "meal_count")
        if meal_count:
            st.session_state.meal_count = meal_count
            return dialog_tree[state]["message"].format(
                name=st.session_state.name,
                event=st.session_state.event,
                people_amount=st.session_state.people_amount,
                meal_count=st.session_state.meal_count
            ), dialog_tree[state]["next_state"], True
        else:
            return "I didn't catch that. How many meals would you like to provide?", state, False

# Function to generate meal plan using OpenAI
def generate_event_plan():
    prompt = f"Create a personalized event plan for someone who wants the least amount of waste possible with the following details:\n\n" \
             f"Name: {st.session_state.name}\n" \
             f"Event: {st.session_state.event}\n" \
             f"People amount: {st.session_state.people_amount}\n" \
             f"Meals per Day: {st.session_state.meal_count}\n\n" \
             f"Please provide a detailed plan for the entire day, including meals and on theme events."

    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[{"role": "system", "content": prompt}],
    max_tokens=500)
    return response.choices[0].message.content

# Function to extract intent and entities for developer insight
def extract_intent_entities(text):
    prompt = f"Extract the intent and entities from the following text:\n\n{text}\n\nProvide the result in the following JSON format:\n{{\"intent\": \"<intent>\", \"entities\": [{{\"entity\": \"<entity>\", \"type\": \"<type>\"}}]}}"
    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[{"role": "system", "content": prompt}],
    max_tokens=100)
    return response.choices[0].message.content

# Function to extract specific entity from the text and validate it
def extract_entity(text, entity_type):
    prompt = f"Extract the {entity_type} from the following text:\n\n{text}\n\nProvide only the {entity_type}."
    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[{"role": "system", "content": prompt}],
    max_tokens=50)
    extracted_entity = response.choices[0].message.content.strip()
    print(f"Extracted entity: {extracted_entity} for type: {entity_type}")  # Debugging statement
    if extracted_entity and validate_entity(extracted_entity, entity_type):
        return extracted_entity
    return None

# Function to validate the extracted entity
def validate_entity(entity, entity_type):
    print(f"Validating entity: {entity} of type: {entity_type}")  # Debugging statement
    if entity_type == "name":
        return entity.isalpha() and len(entity) > 1  # Name should be alphabetic and more than one character
    if entity_type == "event":
        valid_goals = ["birthday party", "reunion", "anniversary", "wedding", \
                        "conference", "meeting", "workshop", "seminar", "concert", \
                        "festival", "holiday celebration", "fundraiser", "gala", \
                        "networking event", "trade show", "product launch", \
                        "team building", "retreat", "webinar", "sports event"]
        return any(goal in entity.lower() for goal in valid_goals)
    if entity_type == "people_amount":
        return entity.isdigit() and 1 <= int(entity) <= 1000
    if entity_type == "meal_count":
        return entity.isdigit() and 1 <= int(entity) <= 10  # Meal count should be a number between 1 and 10
    return False

# Display the existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Function to handle user responses
def handle_user_response(prompt):
    if st.session_state.state:
        user_input = prompt
        st.session_state.messages.append({"role": "user", "content": user_input})
        message, next_state, valid_input = handle_dialog(st.session_state.state, user_input)
        st.session_state.messages.append({"role": "assistant", "content": message})
        if valid_input:
            st.session_state.state = next_state
        st.experimental_rerun()

# Display final meal plan if in the final state
if st.session_state.state == "provide_event_plan":
    meal_plan = generate_event_plan()
    st.session_state.messages.append({"role": "assistant", "content": meal_plan})
    st.session_state.state = None

    # Extract and display intent and entities for developer insight
    insights = extract_intent_entities(meal_plan)
    st.session_state.messages.append({"role": "assistant", "content": f"Developer Insights:\n{insights}"})

# Handle user input at the bottom of the page
if prompt := st.chat_input("Your response:"):
    handle_user_response(prompt)