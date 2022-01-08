# Generate requirements.txt
FROM python:3.9 as micropipenv

RUN pip install micropipenv

COPY Pipfile.lock .
RUN micropipenv requirements --no-dev --no-hashes > requirements.txt


# Final container
FROM python:3.9

WORKDIR /app

COPY --from=micropipenv requirements.txt /app
COPY . /app
RUN pip install -r requirements.txt

CMD ["python3", "-m", "dakap.dakap"]
