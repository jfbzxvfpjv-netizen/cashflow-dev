# Stage 1: build con Maven
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /build
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

# Stage 2: runtime con JRE slim
FROM eclipse-temurin:17-jre-jammy
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=build /build/target/fingermatcher-1.0.0.jar /app/fingermatcher.jar
ENV JAVA_OPTS="-Xmx256m -Xms128m"
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
CMD ["sh", "-c", "java $JAVA_OPTS -jar /app/fingermatcher.jar"]
