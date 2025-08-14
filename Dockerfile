# ---- Builder Stage ----
FROM python:3.8.20-slim-bullseye AS builder

ARG GDAL_VERSION=3.0.4
ARG SOURCE_DIR=/usr/local/src/python-gdal

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential wget automake libtool pkg-config \
        libsqlite3-dev sqlite3 libpq-dev libcurl4-gnutls-dev \
        libproj-dev libxml2-dev libgeos-dev libnetcdf-dev \
        libpoppler-dev libspatialite-dev libhdf4-alt-dev \
        libhdf5-serial-dev libopenjp2-7-dev grass && \
    rm -rf /var/lib/apt/lists/*

# Build and install PROJ
RUN wget "http://download.osgeo.org/proj/proj-6.0.0.tar.gz" && \
    tar -xzf "proj-6.0.0.tar.gz" && \
    mv proj-6.0.0 proj && \
    echo "#!/bin/sh" > proj/autogen.sh && \
    chmod +x proj/autogen.sh && \
    cd proj && ./autogen.sh && \
    CXXFLAGS='-DPROJ_RENAME_SYMBOLS' CFLAGS='-DPROJ_RENAME_SYMBOLS' ./configure --disable-static --prefix=/usr/local && \
    make -j"$(nproc)" && make install && \
    mv /usr/local/lib/libproj.so.15.0.0 /usr/local/lib/libinternalproj.so.15.0.0 && \
    rm /usr/local/lib/libproj.so* && rm /usr/local/lib/libproj.la && \
    ln -s libinternalproj.so.15.0.0 /usr/local/lib/libinternalproj.so.15 && \
    ln -s libinternalproj.so.15.0.0 /usr/local/lib/libinternalproj.so

# Build and install GDAL
RUN mkdir -p "${SOURCE_DIR}" && \
    cd "${SOURCE_DIR}" && \
    wget "http://download.osgeo.org/gdal/${GDAL_VERSION}/gdal-${GDAL_VERSION}.tar.gz" && \
    tar -xvf "gdal-${GDAL_VERSION}.tar.gz" && \
    cd "gdal-${GDAL_VERSION}" && \
    export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH && \
    ./configure --with-python --with-curl --with-openjpeg --without-libtool --with-proj=/usr/local && \
    make -j"$(nproc)" && make install && ldconfig

COPY setup.py requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN pip uninstall -y gdal && \
    pip install --no-cache-dir GDAL==$(gdal-config --version) --global-option=build_ext --global-option="-I/usr/include/gdal"

# ---- Runtime Stage ----
FROM python:3.8.20-slim-bullseye

# Only install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        grass libglib2.0-0 libsm6 libxrender1 \
        libsqlite3-dev sqlite3 libpq-dev libcurl4-gnutls-dev \
        libproj-dev libxml2-dev libgeos-dev libnetcdf-dev \
        libpoppler-dev libspatialite-dev libhdf4-alt-dev \
        libhdf5-serial-dev libopenjp2-7-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy Python packages and binaries from builder
COPY --from=builder /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /usr/share/gdal /usr/share/gdal
COPY --from=builder /usr/local/lib/libgdal* /usr/local/lib/

ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
ENV GDAL_DATA=/usr/share/gdal/
ENV PYTHONPATH=/code:/usr/lib/grass78/etc/python/

# Copy project code
COPY . /code
WORKDIR /code

# Optionally, initialize GRASS data (skip if not needed at build time)
RUN grass --text -c EPSG:4326 grass_data/LatLon/

ENTRYPOINT ["tail", "-f", "/dev/null"]