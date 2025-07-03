# =================================
# Miniconda3
# =================================

FROM continuumio/miniconda3

# ARG ENV_NAME

SHELL ["/bin/bash","-l", "-c"]

WORKDIR /haemostasis_elisa

# Install Miniconda
RUN /opt/conda/bin/conda init bash && \
    /opt/conda/bin/conda config --add channels bioconda && \
    /opt/conda/bin/conda config --add channels conda-forge && \
    /opt/conda/bin/conda update conda -y && \
    /opt/conda/bin/conda clean -afy

# =================================

# Add conda bin to path
ENV PATH=/opt/conda/bin:$PATH

COPY ./environment.yml ./

# Create environment
RUN conda env create -f environment.yml

SHELL ["conda", "run", "-n", "myenv", "/bin/bash", "-c"]

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

COPY ./src .

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "id_ont", "streamlit", "run", "app.py"]
