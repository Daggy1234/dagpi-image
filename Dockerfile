FROM python:3.9.2-slim-buster

COPY ["pyproject.toml", "poetry.lock", "./"]

#RUN apt-get update && \
#    apt-get install -y git gcc glib2.0 libc-dev make curl build-essential gzip 	 libx11-6 libgomp1  libgcc1 libc6   && \
#    python3 -m pip install poetry && \
#    poetry config virtualenvs.create false && \
#    poetry install --no-dev --no-interaction --no-ansi && \
#    pip3 install uvloop && \
#    git clone https://github.com/carlobaldassi/liblqr && \
#    cd liblqr && \
#    ./configure && \
#    make && \
#    make install && \
#    cd .. && \
#    curl https://codeload.github.com/ImageMagick/ImageMagick/tar.gz/7.0.10-51 | tar -xz && \
#    cd ImageMagick-7.0.10-51 && \
#    ./configure --with-lqr && \
#    make && \
#    make install && \
#    ldconfig /usr/local/lib && \
#    magick -version && \
#    cd .. && \
#    rm -R ImageMagick-7.0.10-51 && \
#    rm -R liblqr

RUN apt-get update && \
    apt-get install -y git gcc imagemagick  && \
    python3 -m pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi && \
    pip3 install uvloop

COPY . .

COPY ./start.sh /start.sh

RUN chmod +x /start.sh

COPY ./gunicorn_conf.py /gunicorn_conf.py

COPY ./app /app
WORKDIR /
ENV PYTHONPATH=/app


EXPOSE 5000

CMD ["/start.sh"]