# ---- Builder Stage ----
FROM python:3.12-slim-trixie AS builder

ARG GDAL_VERSION=3.10.3
ARG SOURCE_DIR=/usr/local/src/gdal
ARG NPROC=8

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential wget automake cmake libtool pkg-config \
        libproj-dev libxml2-dev libgeos-dev libnetcdf-dev \
        libhdf4-alt-dev \
        libhdf5-serial-dev bison grass && \
    rm -rf /var/lib/apt/lists/*

# Build and install GDAL
RUN mkdir -p "${SOURCE_DIR}" && \
    cd "${SOURCE_DIR}" && \
    wget "http://download.osgeo.org/gdal/${GDAL_VERSION}/gdal-${GDAL_VERSION}.tar.gz" && \
    tar -xvf "gdal-${GDAL_VERSION}.tar.gz" && \
    cd "gdal-${GDAL_VERSION}" && \
    export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH && \
    mkdir build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local && \
    make -j"${NPROC}" && make install && ldconfig

COPY setup.py requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN pip uninstall -y gdal && \
    pip install --no-cache-dir GDAL==$(gdal-config --version)

# ---- Runtime Stage ----
FROM python:3.12-slim-trixie AS runtime

# Only install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        grass libglib2.0-0 libsm6 libxrender1 \
        libcurl4t64 \
        libproj-dev libxml2 libgeos-c1t64 libgeos3.13.1 libnetcdf22 \
        libhdf4-0-alt \
        libhdf5-310 grass gdal-bin python3-gdal && \
    rm -rf /var/lib/apt/lists/*

# Copy Python packages and binaries from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /usr/share/gdal /usr/share/gdal
COPY --from=builder /usr/local/lib/libgdal* /usr/local/lib/

# Optional but recommended: avoid .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV GDAL_DATA=/usr/share/gdal/
ENV PYTHONPATH=/code:/usr/lib/grass84/etc/python/
ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/lib/grass84/lib
ENV PATH=/usr/lib/grass84/bin:/usr/lib/grass84/scripts:$PATH

# Copy project code
COPY empatia /code/empatia
COPY setup.py requirements.txt /code/
WORKDIR /code

RUN pip install -e .

# Optionally, initialize GRASS data (skip if not needed at build time)
RUN grass --text -c EPSG:4326 grass_data/LatLon/

ENTRYPOINT ["tail", "-f", "/dev/null"]
