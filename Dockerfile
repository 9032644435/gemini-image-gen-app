# Use an official Python runtime as a parent image
FROM python:3.11-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container at /app
COPY . .

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV PORT 8080

# Define the command to run diagnostic checks and then the application
CMD echo "--- DIAGNOSTICS START ---" ; \
    echo "--- Python Executable ---" ; \
    which python ; \
    python --version ; \
    echo "--- PYTHONPATH ---" ; \
    printenv PYTHONPATH ; \
    echo "--- Listing /usr/local/lib/python3.11/site-packages ---" ; \
    ls -l /usr/local/lib/python3.11/site-packages/ | grep google ; \
    echo "--- Trying direct import ---" ; \
    python -c "import google.generativeai; print('Direct import SUCCESSFUL')" || echo "Direct import FAILED" ; \
    echo "--- DIAGNOSTICS END ---" ; \
    echo "--- Starting Gunicorn ---" ; \
    exec python -m gunicorn --bind 0.0.0.0:8080 --timeout 120 app:app
