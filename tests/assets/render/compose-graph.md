# Docker Compose dependency map

## Map

<!-- compose-map:map:start -->

```mermaid
graph LR
  outside(("🌐 External<br/>Internet / LAN"))
  subgraph g__app["app"]
    v__app__web["web"]
    v__app__api["api"]
    v__app__db["db"]
    v__app__cache["cache"]
    vol__app__data[("💾 data")]
    vol__app__dbdata[("💾 dbdata")]
  end
  subgraph g__backup["backup"]
    v__backup__archiver["archiver"]
    vol__backup__archive[("💾 archive")]
  end
  subgraph g__monitoring["monitoring"]
    v__monitoring__prometheus["prometheus"]
    vol__monitoring__metrics[("💾 metrics")]
  end
  subgraph g__proxy["proxy"]
    v__proxy__proxy["proxy"]
    n__edge_net{{"🔗 edge_net"}}
  end
  subgraph g__vpn["vpn"]
    v__vpn__gateway["gateway"]
    v__vpn__torrent["torrent"]
    vol__vpn__downloads[("💾 downloads")]
  end
  n__monitor_net{{"🔗 monitor_net"}}
  host___APP_CONFIG[/"📁 $APP_CONFIG"/]
  host___mnt_backups[/"📁 /mnt/backups"/]
  host___srv_shared[/"📁 /srv/shared"/]
  host___var_run_docker_sock[/"📁 /var/run/docker.sock"/]

  v__app__web -->|depends on| v__app__api
  v__app__web -.->|mounts| vol__app__data
  v__app__web -.->|mounts| host___srv_shared
  v__app__web -.->|mounts| host___APP_CONFIG
  v__app__api -->|depends on| v__app__db
  v__app__api -->|depends on| v__app__cache
  v__app__db -.->|mounts| vol__app__dbdata
  v__backup__archiver -.->|mounts| vol__backup__archive
  v__backup__archiver -.->|mounts| host___mnt_backups
  v__monitoring__prometheus -.->|mounts| vol__monitoring__metrics
  v__proxy__proxy -.->|mounts| host___var_run_docker_sock
  v__vpn__torrent -->|depends on| v__vpn__gateway
  v__vpn__torrent -.->|shares netns| v__vpn__gateway
  v__vpn__torrent -.->|mounts| vol__vpn__downloads

  v__app__web --> n__edge_net
  v__proxy__proxy --> n__edge_net
  v__monitoring__prometheus --> n__monitor_net
  v__vpn__gateway --> n__monitor_net

  v__app__web -->|"publishes :8080/:8443"| outside
  v__app__db -->|"publishes :5432"| outside
  v__monitoring__prometheus -->|"publishes :9090"| outside
  v__proxy__proxy -->|"publishes :80/:443"| outside
  v__vpn__gateway -->|"publishes :51820"| outside

  classDef net fill:#fef3c7,stroke:#d97706,color:#7c2d12;
  classDef out fill:#dcfce7,stroke:#16a34a,color:#14532d;
  classDef vol fill:#e0e7ff,stroke:#4f46e5,color:#312e81;
  classDef host fill:#fae8ff,stroke:#a21caf,color:#701a75;
  class outside out;
  class n__edge_net,n__monitor_net net;
  class vol__app__data,vol__app__dbdata,vol__backup__archive,vol__monitoring__metrics,vol__vpn__downloads vol;
  class host___APP_CONFIG,host___mnt_backups,host___srv_shared,host___var_run_docker_sock host;
```

<!-- compose-map:map:end -->

## Network / ports

<!-- compose-map:network:start -->

```mermaid
graph LR
  outside(("🌐 External<br/>Internet / LAN"))
  subgraph g__app["app"]
    v__app__web["web"]
    v__app__db["db"]
  end
  subgraph g__monitoring["monitoring"]
    v__monitoring__prometheus["prometheus"]
  end
  subgraph g__proxy["proxy"]
    v__proxy__proxy["proxy"]
    n__edge_net{{"🔗 edge_net"}}
  end
  subgraph g__vpn["vpn"]
    v__vpn__gateway["gateway"]
    v__vpn__torrent["torrent"]
  end
  n__monitor_net{{"🔗 monitor_net"}}

  v__vpn__torrent -.->|shares netns| v__vpn__gateway

  v__app__web --> n__edge_net
  v__proxy__proxy --> n__edge_net
  v__monitoring__prometheus --> n__monitor_net
  v__vpn__gateway --> n__monitor_net

  v__app__web -->|"publishes :8080/:8443"| outside
  v__app__db -->|"publishes :5432"| outside
  v__monitoring__prometheus -->|"publishes :9090"| outside
  v__proxy__proxy -->|"publishes :80/:443"| outside
  v__vpn__gateway -->|"publishes :51820"| outside

  classDef net fill:#fef3c7,stroke:#d97706,color:#7c2d12;
  classDef out fill:#dcfce7,stroke:#16a34a,color:#14532d;
  class outside out;
  class n__edge_net,n__monitor_net net;
```

<!-- compose-map:network:end -->

## Volumes / mounts

<!-- compose-map:volumes:start -->

```mermaid
graph LR
  subgraph g__app["app"]
    v__app__web["web"]
    v__app__db["db"]
    vol__app__data[("💾 data")]
    vol__app__dbdata[("💾 dbdata")]
  end
  subgraph g__backup["backup"]
    v__backup__archiver["archiver"]
    vol__backup__archive[("💾 archive")]
  end
  subgraph g__monitoring["monitoring"]
    v__monitoring__prometheus["prometheus"]
    vol__monitoring__metrics[("💾 metrics")]
  end
  subgraph g__proxy["proxy"]
    v__proxy__proxy["proxy"]
  end
  subgraph g__vpn["vpn"]
    v__vpn__torrent["torrent"]
    vol__vpn__downloads[("💾 downloads")]
  end
  host___APP_CONFIG[/"📁 $APP_CONFIG"/]
  host___mnt_backups[/"📁 /mnt/backups"/]
  host___srv_shared[/"📁 /srv/shared"/]
  host___var_run_docker_sock[/"📁 /var/run/docker.sock"/]

  v__app__web -.->|mounts| vol__app__data
  v__app__web -.->|mounts| host___srv_shared
  v__app__web -.->|mounts| host___APP_CONFIG
  v__app__db -.->|mounts| vol__app__dbdata
  v__backup__archiver -.->|mounts| vol__backup__archive
  v__backup__archiver -.->|mounts| host___mnt_backups
  v__monitoring__prometheus -.->|mounts| vol__monitoring__metrics
  v__proxy__proxy -.->|mounts| host___var_run_docker_sock
  v__vpn__torrent -.->|mounts| vol__vpn__downloads

  classDef vol fill:#e0e7ff,stroke:#4f46e5,color:#312e81;
  classDef host fill:#fae8ff,stroke:#a21caf,color:#701a75;
  class vol__app__data,vol__app__dbdata,vol__backup__archive,vol__monitoring__metrics,vol__vpn__downloads vol;
  class host___APP_CONFIG,host___mnt_backups,host___srv_shared,host___var_run_docker_sock host;
```

<!-- compose-map:volumes:end -->

## Compose dependencies

<!-- compose-map:dependencies:start -->

```mermaid
graph LR
  outside(("🌐 External<br/>Internet / LAN"))
  c__app["app"]
  c__monitoring["monitoring"]
  c__proxy["proxy"]
  c__vpn["vpn"]
  n__monitor_net{{"🔗 monitor_net<br/>(no creator)"}}

  c__app -->|"edge_net"| c__proxy
  c__monitoring -->|"monitor_net"| n__monitor_net
  c__vpn -->|"monitor_net"| n__monitor_net

  c__app -->|"publishes web :8080/:8443; db :5432"| outside
  c__monitoring -->|"publishes prometheus :9090"| outside
  c__proxy -->|"publishes proxy :80/:443"| outside
  c__vpn -->|"publishes gateway :51820"| outside

  classDef net fill:#fef3c7,stroke:#d97706,color:#7c2d12;
  classDef out fill:#dcfce7,stroke:#16a34a,color:#14532d;
  class outside out;
  class n__monitor_net net;
```

<!-- compose-map:dependencies:end -->
