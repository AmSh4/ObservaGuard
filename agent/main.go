package main

import (
	"encoding/json"
	"log"
	"math/rand"
	"net/http"
	"os"
	"time"
)

type Stat struct {
	Ts int64 `json:"ts"`
	Node string `json:"node"`
	Cpu float64 `json:"cpu"`
	Mem float64 `json:"mem"`
	Pods int `json:"pods"`
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request){
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"ok":true}`))
	})
	mux.HandleFunc("/stats", func(w http.ResponseWriter, r *http.Request){
		w.Header().Set("Content-Type", "application/json")
		mock := os.Getenv("MOCK_MODE") == "true"
		node := os.Getenv("NODE_NAME")
		if node == "" { node = "local-node" }
		cpu := 0.3 + rand.Float64()*0.6
		mem := 0.4 + rand.Float64()*0.5
		pods := 5 + rand.Intn(20)
		if !mock {
			// In real cluster you'd read from cgroup or kubelet summary API
		}
		res := Stat{Ts: time.Now().Unix(), Node: node, Cpu: cpu, Mem: mem, Pods: pods}
		json.NewEncoder(w).Encode(res)
	})
	port := os.Getenv("AGENT_PORT")
	if port == "" { port = "8080" }
	log.Printf("agent listening on :%s", port)
	http.ListenAndServe(":"+port, mux)
}
