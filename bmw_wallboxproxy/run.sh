#!/usr/bin/with-contenv bashio

set -euo pipefail

export PATH=/opt/venv/bin:${PATH}
export APP_ENV_FILE=/data/bmw_wallboxproxy.env
export MODBUS_LISTEN_HOST=0.0.0.0
export MODBUS_LISTEN_PORT=502
export WEBAPP_HOST=0.0.0.0
export WEBAPP_PORT=8099
export WEBAPP_SSL_MODE=off
export WEBAPP_USE_RELOADER=false
export HA_TOKEN="$(bashio::config 'ha_token')"
export HA_URL=http://supervisor/core/api
export HA_VERIFY_TLS=false
export HA_USE_SUPERVISOR=true
export MODBUS_TRANSPORT_MODE="$(bashio::config 'transport_mode')"
export MODBUS_FLOAT_WORD_ORDER="$(bashio::config 'float_word_order')"
export MODBUS_REGISTER_ALIAS_MODE="$(bashio::config 'register_alias_mode')"
export HA_ENTITY_U1="$(bashio::config 'u1_entity')"
export HA_ENTITY_U2="$(bashio::config 'u2_entity')"
export HA_ENTITY_U3="$(bashio::config 'u3_entity')"
export HA_ENTITY_I1="$(bashio::config 'i1_entity')"
export HA_ENTITY_I2="$(bashio::config 'i2_entity')"
export HA_ENTITY_I3="$(bashio::config 'i3_entity')"
export HA_ENTITY_P_TOTAL="$(bashio::config 'p_total_entity')"
export HA_ENTITY_FREQ="$(bashio::config 'freq_entity')"
export HA_ENTITY_P1="$(bashio::config 'p1_entity')"
export HA_ENTITY_P2="$(bashio::config 'p2_entity')"
export HA_ENTITY_P3="$(bashio::config 'p3_entity')"
export HA_ENTITY_E_IMPORT_TOTAL="$(bashio::config 'e_import_total_entity')"
export HA_ENTITY_E_EXPORT_TOTAL="$(bashio::config 'e_export_total_entity')"
export HA_ENTITY_PAUSE="$(bashio::config 'pause_entity')"
export HA_ENTITY_POWER_OFFSET="$(bashio::config 'power_offset_entity')"

bashio::log.info "Starting BMW Wallbox Proxy add-on"
bashio::log.info "Web UI is served over Home Assistant ingress on internal HTTP port 8099"
bashio::log.info "Runtime settings are sourced from the Home Assistant add-on configuration"

exec /opt/venv/bin/python /app/app.py