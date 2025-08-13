FROM python:3.10-slim AS builder

ARG SOURCE_DIR=/usr/local/src/python-gdal
ARG BUILD_PACKAGES="vim bzip2 unzip make gcc g++ git libglib2.0-0 libsm6 libxrender1 build-essential wget automake libtool pkg-config libsqlite3-dev sqlite3 libpq-dev libcurl4-gnutls-dev libproj-dev libxml2-dev libgeos-dev libnetcdf-dev libpoppler-dev libspatialite-dev libhdf4-alt-dev libhdf5-serial-dev libopenjp2-7-dev"

# Install system dependencies and build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends $BUILD_PACKAGES grass grass-doc && \
    apt-get install -y --no-install-recommends gdal-bin libgdal-dev python3-gdal && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

COPY setup.py requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Fix GDAL Python bindings
RUN pip uninstall gdal -y
RUN pip install GDAL==$(gdal-config --version)

# ---- Final stage ----
FROM python:3.10-slim

# Install only runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends grass grass-doc libglib2.0-0 libsm6 libxrender1 libsqlite3-dev sqlite3 libpq-dev libcurl4-gnutls-dev libproj-dev libxml2-dev libgeos-dev libnetcdf-dev libpoppler-dev libspatialite-dev libhdf4-alt-dev libhdf5-serial-dev libopenjp2-7-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /usr/share/gdal /usr/share/gdal

ENV GDAL_DATA=/usr/share/gdal/
ENV PYTHONPATH=/code:/usr/lib/grass84/etc/python/

# Copy project code
COPY . /code
WORKDIR /code

# Initialize GRASS data
RUN grass --text -c EPSG:4326 grass_data/LatLon/

ENTRYPOINT ["/code/docker_entrypoint.sh"]