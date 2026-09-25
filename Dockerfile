# One stage per Odoo source, `make odoo-image VERSION=...` picks one with the
# BASE build arg (see scripts/build-args.sh). BuildKit only builds that stage.
#
# Released images are pinned to a dated build so the code matches the schema in
# the persisted database. After bumping, run `make reset` (or update modules
# with -u all). A different series always needs `make reset`.
# The stage to build on, an ARG before the first FROM so FROM can use it
ARG BASE=release-19

FROM odoo:19.0-20260908 AS release-19

# The newest dated nightly deb of a series from nightly.odoo.com, installed over
# the newest released image, which brings the system packages and entrypoint
FROM release-19 AS nightly
ARG NOODLE_SERIES
ARG NOODLE_RELEASE
USER root
RUN curl -fsSLo /tmp/odoo.deb \
      "https://nightly.odoo.com/${NOODLE_SERIES}/nightly/deb/odoo_${NOODLE_SERIES}.${NOODLE_RELEASE}_all.deb" \
    && apt-get update \
    && apt-get install -y --no-install-recommends /tmp/odoo.deb \
    && rm -rf /tmp/odoo.deb /var/lib/apt/lists/*
ENV ODOO_VERSION=${NOODLE_SERIES}

# A commit of odoo/odoo (usually master) from git. Laid out like the deb: the
# addons merged into odoo/addons, the package in place of the packaged one.
FROM release-19 AS master
ARG NOODLE_COMMIT
USER root
RUN curl -fsSL "https://github.com/odoo/odoo/archive/${NOODLE_COMMIT}.tar.gz" | tar -xz -C /opt \
    && mv "/opt/odoo-${NOODLE_COMMIT}" /opt/odoo \
    && cp -a /opt/odoo/addons/. /opt/odoo/odoo/addons/ \
    && rm -rf /opt/odoo/addons /usr/lib/python3/dist-packages/odoo \
    && ln -s /opt/odoo/odoo /usr/lib/python3/dist-packages/odoo \
    && apt-get update \
    && sed -n '/^Depends:/,/^[A-Z]/p' /opt/odoo/debian/control | grep -oE 'python3-[a-z0-9.-]+' | sort -u \
      | xargs apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
ENV ODOO_VERSION=master

FROM ${BASE}

USER root

# en_US.UTF-8 from the base image is not generated, psql warns about it
ENV LANG=C.UTF-8

COPY --chmod=0644 odoo/odoo.conf /etc/odoo/odoo.conf
# Custom Dynamist modules, install them by adding them to ODOO_MODULES.
# Not /mnt/extra-addons, which is a volume in the base image and would go stale.
COPY addons/ /mnt/dynamist-addons/
COPY --chmod=0755 odoo/entrypoint.sh odoo/init-odoo.sh /opt/noodle/
COPY --chmod=0755 odoo/lib/ /opt/noodle/lib/
COPY odoo/seed/ /opt/noodle/seed/

RUN chown odoo /etc/odoo/odoo.conf

USER odoo

ENTRYPOINT ["/opt/noodle/entrypoint.sh"]
CMD ["odoo"]
