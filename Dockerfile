# Use the official Python base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install system dependencies
RUN apt-get update && apt-get install -y libgl1-mesa-glx

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code to the working directory
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Set the entry point for the container
ENTRYPOINT [ "python" ]

# Set the command to run your Flask app
CMD [ "app.py" ]
