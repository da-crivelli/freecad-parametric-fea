FROM mcr.microsoft.com/devcontainers/base:bullseye
RUN sudo apt update 
RUN sudo apt install python3-distutils
RUN sudo apt install -y freecad
RUN curl -sSL https://install.python-poetry.org | python3 -
RUN pip install -r requirements.txt