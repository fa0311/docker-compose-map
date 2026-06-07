# Docker Compose dependency map

## Map

<!-- compose-map:map:start -->
```mermaid
graph TD
  outside(("🌐 External<br/>Internet / LAN"))
  subgraph g__app["app"]
    v__app__web["web"]
    v__app__db["db"]
    vol__app__data[("💾 data")]
  end
  subgraph g__proxy["proxy"]
    v__proxy__proxy["proxy"]
    n__edge_net{{"🔗 edge_net"}}
  end
  host___srv_shared[/"📁 /srv/shared"/]

  v__app__web -->|depends on| v__app__db
  vol__app__data -.-> v__app__web
  host___srv_shared -.-> v__app__web

  v__app__db --> n__edge_net
  v__app__web --> n__edge_net
  v__proxy__proxy --> n__edge_net

  outside -->|"publishes :8080"| v__app__web

  classDef net fill:#fef3c7,stroke:#d97706,color:#7c2d12;
  classDef out fill:#dcfce7,stroke:#16a34a,color:#14532d;
  classDef vol fill:#e0e7ff,stroke:#4f46e5,color:#312e81;
  classDef host fill:#fae8ff,stroke:#a21caf,color:#701a75;
  class outside out;
  class n__edge_net net;
  class vol__app__data vol;
  class host___srv_shared host;
```
<!-- compose-map:map:end -->

## Network / ports

<!-- compose-map:network:start -->
```mermaid
graph TD
  outside(("🌐 External<br/>Internet / LAN"))
  subgraph g__app["app"]
    v__app__web["web"]
    v__app__db["db"]
  end
  subgraph g__proxy["proxy"]
    v__proxy__proxy["proxy"]
    n__edge_net{{"🔗 edge_net"}}
  end


  v__app__db --> n__edge_net
  v__app__web --> n__edge_net
  v__proxy__proxy --> n__edge_net

  outside -->|"publishes :8080"| v__app__web

  classDef net fill:#fef3c7,stroke:#d97706,color:#7c2d12;
  classDef out fill:#dcfce7,stroke:#16a34a,color:#14532d;
  class outside out;
  class n__edge_net net;
```
<!-- compose-map:network:end -->

## Volumes / mounts

<!-- compose-map:volumes:start -->
```mermaid
graph TD
  subgraph g__app["app"]
    v__app__web["web"]
    vol__app__data[("💾 data")]
  end
  host___srv_shared[/"📁 /srv/shared"/]

  vol__app__data -.-> v__app__web
  host___srv_shared -.-> v__app__web

  classDef vol fill:#e0e7ff,stroke:#4f46e5,color:#312e81;
  classDef host fill:#fae8ff,stroke:#a21caf,color:#701a75;
  class vol__app__data vol;
  class host___srv_shared host;
```
<!-- compose-map:volumes:end -->

## Compose dependencies

<!-- compose-map:dependencies:start -->
```mermaid
graph TD
  c__app["app"]
  c__proxy["proxy"]

  c__app -->|"edge_net"| c__proxy

  classDef net fill:#fef3c7,stroke:#d97706,color:#7c2d12;
```
<!-- compose-map:dependencies:end -->
