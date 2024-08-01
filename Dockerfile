FROM python:3.11.9-bookworm

# Set the environment variable to suppress interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Set up a virtual display
ENV DISPLAY=:99

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libvtk9-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libosmesa6-dev \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    libxrender1 \
    xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY . .

RUN pip install -r requirements.txt

# Rebuild TVTK to ensure compatibility
RUN pip install --force-reinstall mayavi

CMD Xvfb :99 -screen 0 1024x768x24 & python gcode2png.py  BR-YBU-SM.gcode thumbnail.png
