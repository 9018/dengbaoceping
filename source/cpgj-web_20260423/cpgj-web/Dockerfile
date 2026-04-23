FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY go.mod ./
COPY cmd ./cmd
COPY static ./static
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /out/upload-web ./cmd/web

FROM scratch
WORKDIR /app
COPY --from=builder /out/upload-web /upload-web
EXPOSE 8088
ENTRYPOINT ["/upload-web"]
