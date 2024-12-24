FROM python:3.10

ENV PYTHONPYCACHEPREFIX=/tmp/python
ENV PYTHONUTF8=1
ENV NUMBA_CACHE_DIR=/tmp/numba_cache

RUN <<EOT
set -e

curl https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n7.1-latest-linux64-gpl-7.1.tar.xz \
  -sSfL -o /tmp/ffmpeg.tar.xz
tar -xf /tmp/ffmpeg.tar.xz -C /usr/local/src
find /usr/local/src/ffmpeg-n* \
  -type f \( -name ffmpeg -o -name ffprobe -o -name qt-faststart \) \
  -exec ln -s "{}" /usr/bin/ ';'
rm -rf /tmp/ffmpeg.tar.xz
EOT

RUN <<EOT
set -e

python -m pip install --upgrade pip
pip install pipenv
EOT

WORKDIR /var/app/src

COPY src/Pipfile* ./

RUN <<EOT
set -e

pipenv install -v --deploy --system
pipenv --clear
EOT

COPY src/ .

VOLUME /tmp

#RUN <<EOT
#set -e
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
