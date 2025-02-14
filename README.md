### Available to play around with for FREE: https://huggingface.co/spaces/Mr-Geo/Rover-GPT

# 1920s Rover Engineer AI
## Description
This repository contains a FastAPI application designed to simulate a 1920s Rover Engineer AI. The application features a user-friendly chat interface where users can interact with an AI to ask questions related to rover engineering. The backend integrates OpenAI's API to process and respond to user queries. The front-end is designed with a dark theme, reminiscent of the 1920s aesthetic, and built using HTML, Tailwind CSS, and JavaScript.

## Features
Chat interface for user-AI interaction
Integration with OpenAI's API for AI responses
Dark-themed UI inspired by the 1920s aesthetic
Responsive design for various device sizes
Installation
To run this project locally, follow these steps:

## Prerequisites
Python 3.8+
pip (Python package manager)
Setup
Clone the repository:
bash

git clone https://github.com/[YourUsername]/1920s-Rover-Engineer-AI.git
Navigate to the project directory:
bash

cd 1920s-Rover-Engineer-AI
Install the required Python packages:

pip install -r requirements.txt

## Usage
To start the FastAPI server, run the following command in the project directory:

css

uvicorn main:app --reload
The application will be available at http://localhost:8000.

## Configuration
Before running the application, ensure you set up the following environment variables:

API_KEY: Your OpenAI API key
ASSISTANT_ID: The ID of your OpenAI Assistant
Contributing
Contributions to this project are welcome. Please follow these steps to contribute:

## Fork the repository
Create a new branch (git checkout -b feature/YourFeature)
Commit your changes (git commit -am 'Add some feature')
Push to the branch (git push origin feature/YourFeature)
Open a Pull Request
