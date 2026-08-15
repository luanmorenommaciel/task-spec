FROM python@sha256:adafcc17694d715c905b4c7bebd96907a1fd5cf183395f0ebc4d3428bd22d92d

RUN apt-get update \
    && apt-get install --no-install-recommends -y bash ca-certificates git openssl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 65532 taskspec \
    && useradd --uid 65532 --gid 65532 --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin taskspec

COPY VERSION /opt/task-spec/VERSION
COPY bin /opt/task-spec/bin
COPY src /opt/task-spec/src
COPY spec /opt/task-spec/spec
COPY templates /opt/task-spec/templates

RUN chmod -R a=rX /opt/task-spec

USER 65532:65532
WORKDIR /workspace
ENTRYPOINT ["/opt/task-spec/bin/taskspec"]
