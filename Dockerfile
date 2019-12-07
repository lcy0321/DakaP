FROM kennethreitz/pipenv
COPY bot-token Pipfile Pipfile.lock dakap.py /app/
CMD ["python", "./dakap.py"]
