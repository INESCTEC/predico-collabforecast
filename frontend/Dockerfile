# Stage 1: Build the React app
FROM node:18-alpine as build

WORKDIR /app

# Pass build arguments to React
ARG REACT_APP_API_URL
ARG REACT_APP_BASE_URL
ARG REACT_APP_EMAIL

ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_BASE_URL=$REACT_APP_BASE_URL
ENV REACT_APP_EMAIL=$REACT_APP_EMAIL

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci --production

# Copy the rest of the app and build
COPY . ./

# Build the React app
RUN npm run build
