FROM python@sha256:adafcc17694d715c905b4c7bebd96907a1fd5cf183395f0ebc4d3428bd22d92d

ARG TARGETARCH
ARG OMP_VERSION=17.3.3
ARG OMP_LINUX_AMD64_SHA256=25d642d35cf07a6b94336da94fa6d69b7a0a8b2f1b865ccf92e770ba37aaa606
ARG OMP_LINUX_ARM64_SHA256=b2e8ae942cbd8aee2cabea62c96166753ca9b258c1314897ab81ef8f18fd090e

RUN apt-get update \
    && apt-get install --no-install-recommends -y bash ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 65532 taskmesh \
    && useradd --uid 65532 --gid 65532 --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin taskmesh \
    && case "$TARGETARCH" in \
         amd64) omp_arch=x64; omp_sha="$OMP_LINUX_AMD64_SHA256" ;; \
         arm64) omp_arch=arm64; omp_sha="$OMP_LINUX_ARM64_SHA256" ;; \
         *) echo "unsupported TaskMesh worker architecture: $TARGETARCH" >&2; exit 1 ;; \
       esac \
    && curl -fsSL "https://github.com/can1357/oh-my-pi/releases/download/v${OMP_VERSION}/omp-linux-${omp_arch}" -o /usr/local/bin/omp \
    && echo "$omp_sha  /usr/local/bin/omp" | sha256sum -c - \
    && chmod 0555 /usr/local/bin/omp

COPY release/mesh/worker-entrypoint.sh /opt/taskmesh/worker-entrypoint.sh
RUN chmod 0555 /opt/taskmesh/worker-entrypoint.sh \
    && mkdir -p /workspace \
    && chown 65532:65532 /workspace

USER 65532:65532
WORKDIR /workspace
ENTRYPOINT ["/opt/taskmesh/worker-entrypoint.sh"]
