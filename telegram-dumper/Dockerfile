FROM python:3.10

ENV PYTHONPYCACHEPREFIX=/tmp/python
ENV PYTHONUTF8=1
ENV PIPENV_VENV_IN_PROJECT=1

RUN <<EOT
set -e

python -m pip install --upgrade pip
pip install pipenv
EOT

WORKDIR /var/app

COPY Pipfile* ./

RUN <<EOT
set -e

pipenv install -v --deploy
pipenv --clear
EOT

ENV PATH="/var/app/.venv/bin:$PATH"

WORKDIR /var/app/src

COPY src/ .

VOLUME /tmp

CMD ["bash"]
