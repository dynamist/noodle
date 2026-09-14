# Pinned to a dated build so the code matches the schema in the persisted
# database. After bumping, run `make reset` (or update modules with -u all).
ARG ODOO_IMAGE=odoo:19.0-20260908
FROM ${ODOO_IMAGE}

USER root

# en_US.UTF-8 from the base image is not generated, psql warns about it
ENV LANG=C.UTF-8

COPY --chmod=0644 odoo/odoo.conf /etc/odoo/odoo.conf
# Custom Dynamist modules, install them by adding them to ODOO_MODULES.
# Not /mnt/extra-addons, which is a volume in the base image and would go stale.
COPY addons/ /mnt/dynamist-addons/
COPY --chmod=0755 odoo/entrypoint.sh odoo/init-odoo.sh /opt/odoo-dev/
COPY --chmod=0755 odoo/lib/ /opt/odoo-dev/lib/
COPY odoo/seed/ /opt/odoo-dev/seed/

RUN chown odoo /etc/odoo/odoo.conf

USER odoo

ENTRYPOINT ["/opt/odoo-dev/entrypoint.sh"]
CMD ["odoo"]
