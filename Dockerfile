FROM python:3.8-slim-buster
COPY install-packages.sh .
COPY requirements.txt .
COPY env_file .
COPY ftp_file_uploader.py .
RUN /bin/bash -c 'ls -la; chmod +x install-packages.sh; ls -la'
RUN ./install-packages.sh
CMD [ "python", "./ftp_file_uploader.py" ]
