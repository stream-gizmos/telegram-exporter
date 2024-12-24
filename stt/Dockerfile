FROM python:3.10

ENV PYTHONPYCACHEPREFIX=/tmp/python
ENV PYTHONUTF8=1
ENV NUMBA_CACHE_DIR=/tmp/numba_cache

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

#RUN <<EOT
#set -ex
#
#apt update
#apt install -y \
#  libogg-dev \
#  libopusfile-dev
#
#pip install numpy
#pip install git+https://github.com/TeamPyOgg/PyOgg.git#egg=PyOgg
#EOT

CMD ["bash"]
