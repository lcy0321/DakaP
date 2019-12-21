FROM kennethreitz/pipenv
COPY . /app/
CMD ["python3", "-m", "dakap.dakap"]
