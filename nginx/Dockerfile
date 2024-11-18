FROM nginx

RUN rm /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/

RUN rm /etc/nginx/conf.d/default.conf
COPY project.conf /etc/nginx/conf.d/

COPY ssl/localhost.pem /etc/nginx/ssl/certificate.pem
COPY ssl/localhost.key /etc/nginx/ssl/private.key

COPY docs/quick-guide /usr/share/nginx/quick-guide

# Expose port 443
EXPOSE 443