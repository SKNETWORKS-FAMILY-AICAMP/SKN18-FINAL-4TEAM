# EC2 deployment helper for docker-compose.prod.yml
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker/docker-compose.prod.yml"

if [ ! -f "$ROOT_DIR/.env" ]; then
  echo "Missing .env at repo root. Copy .env.sample and fill values."
  exit 1
fi

cd "$ROOT_DIR/docker"

docker compose -f "$COMPOSE_FILE" build

docker compose -f "$COMPOSE_FILE" up -d

# run migrations after containers are up
sleep 2
docker compose -f "$COMPOSE_FILE" exec backend python manage.py migrate

# optional: create admin user
# docker compose -f "$COMPOSE_FILE" exec backend python manage.py createsuperuser

echo "Deployment done. Check: http://<EC2_PUBLIC_IP>/"
