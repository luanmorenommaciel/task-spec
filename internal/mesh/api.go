package mesh

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"time"
)

func HTTPClient(socket string) *http.Client {
	transport := &http.Transport{
		DialContext: func(ctx context.Context, _, _ string) (net.Conn, error) {
			return (&net.Dialer{}).DialContext(ctx, "unix", socket)
		},
	}
	return &http.Client{Transport: transport, Timeout: 10 * time.Second}
}

func Health(socket string) (APIIdentity, error) {
	response, err := HTTPClient(socket).Get("http://taskmesh/v1/health")
	if err != nil {
		return APIIdentity{}, err
	}
	defer response.Body.Close()
	var identity APIIdentity
	if response.StatusCode != http.StatusOK {
		return identity, fmt.Errorf("TaskMesh health returned %s", response.Status)
	}
	return identity, json.NewDecoder(response.Body).Decode(&identity)
}

func Call(socket string, request CommandRequest) (CommandResponse, error) {
	reader, writer := io.Pipe()
	go func() {
		err := json.NewEncoder(writer).Encode(request)
		writer.CloseWithError(err)
	}()
	response, err := HTTPClient(socket).Post("http://taskmesh/v1/command", "application/json", reader)
	if err != nil {
		return CommandResponse{}, err
	}
	defer response.Body.Close()
	var result CommandResponse
	if err := json.NewDecoder(response.Body).Decode(&result); err != nil {
		return result, err
	}
	return result, nil
}
