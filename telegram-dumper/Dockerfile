FROM python:3.10

ENV PYTHONPYCACHEPREFIX=/tmp/python
ENV PYTHONUTF8=1

RUN set -e; \
    python -m pip install --upgrade pip; \
    pip install pipenv

WORKDIR /var/app/src

COPY src/Pipfile* ./

RUN set -e; \
    pipenv install -v --deploy --system; \
    pipenv --clear

COPY src/ .

VOLUME /tmp

CMD ["bash"]
