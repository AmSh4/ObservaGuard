FROM golang:1.22 as builder
WORKDIR /app
COPY . .
RUN go mod init agent && go mod tidy || true
RUN go build -o agent

FROM gcr.io/distroless/base-debian12
WORKDIR /app
COPY --from=builder /app/agent /app/agent
EXPOSE 8080
USER nonroot:nonroot
ENTRYPOINT ["/app/agent"]
