FROM node:22-alpine AS builder

WORKDIR /app

ARG NEXT_PUBLIC_BACKEND_URL

ENV NEXT_PUBLIC_BACKEND_URL=${NEXT_PUBLIC_BACKEND_URL}

COPY package.json package-lock.json ./

RUN npm install --force

COPY . .

RUN npm run build

FROM node:22-alpine

WORKDIR /app

COPY --from=builder /app ./

CMD ["npm", "start"]
