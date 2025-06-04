FROM ecpe4s/ubuntu20.04-runner-x86_64:2022-05-01

ARG BUILD_DATE
ARG COMMIT

RUN git clone --recursive https://github.com/exawind/exawind-manager \
 && git -C exawind-manager checkout $COMMIT

ENV E4S_MACHINE=1 
ENV EXAWIND_MANAGER=/exawind-manager

WORKDIR /exawind-manager/scripts
RUN ["/bin/bash", "./ci-creator.sh"]

WORKDIR /
RUN apt update -y \
 && apt install -y clangd \
 && apt clean -y

RUN echo export EXAWIND_MANAGER=$EXAWIND_MANAGER >> /etc/bash.bashrc \
 && echo export E4S_MACHINE=1 >> /etc/bash.bashrc \
 && echo ". \$EXAWIND_MANAGER/start.sh" >> /etc/bash.bashrc \
 && echo spack-start >> /etc/bash.bashrc

LABEL io.e4s.build-date=${BUILD_DATE}

