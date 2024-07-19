# Distributed Load Testing System

## Goal

Design and build a distributed load-testing system that co-ordinates between
multiple driver nodes to run a highly concurrent, high-throughput load test on a
web server. This system will use Kafka as a communication service.

## Application Architecture

![Application Architecture](https://github.com/user-attachments/assets/f4302dc4-a8bf-4a8d-af1b-4b6f68439fff)

The orchestrator node and driver node are implemented as separate processes
(you do not need to provision separate VMs for each)
The Orchestrator node and the Driver node must communicate via Kafka (see
topic and message descriptor)
The Orchestrator node and driver node must roughly have the above described
components.

## Functionality

The system uses Kafka as a single point of communication, publishing and
subscribing roughly to the below topics.

All nodes take the Kafka IP Address and the Orchestrator node IP Address as
command-line arguments.

All Nodes possess a unique ID that they use to register themselves, and
are capable of generating unique IDs as necessary.

The system supports the two following types of load tests:

- Tsunami testing: The user is able to set a delay interval between
  each request, and the system maintains this gap between each request on
  each node
- Avalanche testing: All requests are sent as soon as they are ready in
  first-come first-serve order

The user must provide a target throughput per driver node (X requests per
second) and the implementation respects that. The user must provide a
total number of requests to be run per driver node in the test
configuration.
The test stops on each driver node once the responses to all
of these requests have been recieved.

There is no time bound for when tests can stop. It depends purely on when
all responses are recieved.

Load tests stop when a fixed number of requests per driver node are run in
parallel. There is no time bound, as this cannot be controlled by the load
testing tool, but rather depends on the implementation of the Target Server.

The system supports observability.

The Orchestrator node knows how many requests each driver node has sent,
updated at a maximum interval of \textbf{one second}.

The Orchestrator node is able to show a dashboard with aggregated {min,
max, mean, median, mode} response latency across all (driver) nodes, and for
each (driver) node

Both the driver node and the orchestrator node have a metrics store.

It is possible to run a test with a minimum of three (one
orchestrator, two driver) and a maximum of nine (one orchestrator, 8 driver)
nodes.
It is possible to change the number of driver nodes between tests.


## Code
This implementation of an Orchestrator Node

- Exposes a REST API to view and control different tests
- Can trigger a load test
- Can report statistics for a current load test
- Implements a Runtime controller that
  - Handles Heartbeats from the Driver Nodes (sent after the Driver Nodes
have been connected and until they are disconnected)
  - Is responsible for co-ordinating between driver nodes to trigger load
tests
recieves metrics from the driver nodes and stores them in the metrics
store

This implementation of a Driver node

- Sends requests to the target webserver as indicated by the Orchestrator
node records statistics for `{mean, median, min, max}` response time
sends said results back to the Orchestrator node
- Implements a communication layer that talks to the central Kafka instance,
implemented around a Kafka Client.

An implementation of a target HTTP server

- An endpoint to test (`/ping`)
- A metrics endpoint to see the number of requests sent and responses sent
(`/metrics`)

You can find a sample implementation of a target server here, which you can use
for your initial testing. This comes with both the `/ping` and `/metrics`
endpoints baked in -
https://github.com/anirudhRowjee/bd2023-load-testing-server

## JSON Message and Topic Descriptor Format

All Nodes must register themselves through the `register` topic

- Register message format

{
  "node_id": "<span style='color: #1f77b4; font-weight: bold;'>&lt;NODE ID HERE&gt;</span>",
  "node_IP": "<span style='color: #ff7f0e; font-weight: bold;'>&lt;NODE IP ADDRESS (with port) HERE&gt;</span>",
  "message_type": "<span style='color: #2ca02c; font-weight: bold;'>DRIVER_NODE_REGISTER</span>"
}

The Orchestrator node must publish a message to the `test_config` topic to send
out test configuration to all driver nodes

- TestConfig message format


{
  "test_id": "<span style='color: #1f77b4; font-weight: bold;'>&lt;RANDOMLY GENERATED UNIQUE TEST ID&gt;</span>",
  "test_type": "<span style='color: #ff7f0e; font-weight: bold;'>&lt;AVALANCHE|TSUNAMI&gt;</span>",
  "test_message_delay": "<span style='color: #2ca02c; font-weight: bold;'>&lt;0 | CUSTOM_DELAY (only applicable in case of Tsunami testing)&gt;</span>",
  "message_count_per_driver": "<span style='color: #d62728; font-weight: bold;'>&lt;A NUMBER&gt;</span>"
}

The Orchestrator node must publish a message to the `trigger` topic to begin the
load test, and as soon as the drivers recieve this message, they have to begin
the load test

- Trigger message format

{
  "test_id": "<span style='color: #1f77b4; font-weight: bold;'>&lt;RANDOMLY GENERATED UNIQUE TEST ID&gt;</span>",
  "trigger": "<span style='color: #ff7f0e; font-weight: bold;'>&lt;YES&gt;</span>"
}

The driver nodes must publish their aggregate metrics to the `metrics` topic as
the load test is going on at a regular interval

- Metrics message format

{
  "node_id": "<span style='color: #1f77b4; font-weight: bold;'>&lt;RANDOMLY GENERATED UNIQUE NODE ID&gt;</span>",
  "test_id": "<span style='color: #ff7f0e; font-weight: bold;'>&lt;TEST ID&gt;</span>",
  "report_id": "<span style='color: #2ca02c; font-weight: bold;'>&lt;RANDOMLY GENERATED ID FOR EACH METRICS MESSAGE&gt;</span>",
  
  `//latencies in ms`
  
  
  "metrics": {
    "mean_latency": "<span style='color: #d62728; font-weight: bold;'>&lt;VALUE&gt;</span>",
    "median_latency": "<span style='color: #9467bd; font-weight: bold;'>&lt;VALUE&gt;</span>",
    "min_latency": "<span style='color: #8c564b; font-weight: bold;'>&lt;VALUE&gt;</span>",
    "max_latency": "<span style='color: #e377c2; font-weight: bold;'>&lt;VALUE&gt;</span>"
  }
}

The driver nodes must also publish their heartbeats to the `heartbeat` topic as
the load test is going on at a regular interval

- Heartbeat Message Format

{
  "node_id": "<span style='color: #1f77b4; font-weight: bold;'>&lt;RANDOMLY GENERATED UNIQUE NODE ID&gt;</span>",
  "heartbeat": "<span style='color: #ff7f0e; font-weight: bold;'>&lt;YES&gt;</span>",
  "timestamp": "<span style='color: #2ca02c; font-weight: bold;'>&lt;Heartbeat Timestamp&gt;</span>"
}









