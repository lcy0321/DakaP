FROM python:3.7
WORKDIR /usr/src/app
COPY bot-token Pipfile Pipfile.lock dakap.py ./
RUN pip install --no-cache-dir pipenv
RUN pipenv install --system --ignore-pipfile
CMD ["python", "./dakap.py"]
