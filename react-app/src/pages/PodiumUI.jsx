import { useState, useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import { Link } from "react-router-dom";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import "./PodiumUI.css";

const PodiumUI = () => {
  const [inputValue, setInputValue] = useState("");
  const [showPodium, setShowPodium] = useState(false);
  const [animateCards, setAnimateCards] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCard, setSelectedCard] = useState(null);
  const [podiumData, setPodiumData] = useState(null);
  const [streamData, setStreamData] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);


  const { logout } = useAuth();
  const handleLogout = () => logout();

  
  const API_URL = import.meta.env.VITE_APP_BACKEND_ADDRESS; 
  
  class RetriableError extends Error { }
  class FatalError extends Error { }

  const [startIndex, setStartIndex] = useState(0);
  const itemsPerPage = 3; // Number of items to show at a time

  const handleKeyPress = async (event) => {
    if (event.key === "Enter" && inputValue.trim() !== "" && !isSubmitting) {
      setIsSubmitting(true);
      setError("")  
      try {
            if ("geolocation" in navigator) {
                // Wait for location before proceeding
                const position = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject);
                });

                const userLocation = {
                    lat: position.coords.latitude,
                    lon: position.coords.longitude,
                };

                const token = localStorage.getItem("token");

                await fetchEventSource(`${API_URL}/api/generate`, {
                  method: "POST",
                  headers: {
                      "Content-Type": "application/json",
                      "Authorization": `Bearer ${token}`
                  },
                  body: JSON.stringify({
                      input: inputValue,
                      location: userLocation
                  }),

                  async onopen(response) {
                    if (response.ok && response.headers.get("content-type")?.includes("text/event-stream")) {
                        console.log("Streaming started...");
                    } else if (response.status === 401) {
                        //await a promise, and parse to json to access the message 'detail'
                        const error = await response.json()
                        throw new FatalError(error.detail);
                    } else {
                        throw new RetriableError();
                    }
                  },

                  onmessage(event) {
                    const data = JSON.parse(event.data);

                    if (data.status === 429) {
                      setError(data.output);
                      throw new FatalError(data.output);
                  }
  
                    if (data.status === "processing" || data.status === "end") {
                        setStreamData(data.output);
                    }

                    if (data.status === "complete") {
                        console.log("Podium data:", data.output);
                        setPodiumData(data.output)
                        setStreamData("");
                        setShowPodium(true);
                        setStartIndex(0);
                    }
                  },
  
                

                  onerror(err) {
                      if (err instanceof FatalError) {
                        setError(err.message)  
                        throw err; // rethrow to stop the operation
                      } else {
                          // do nothing to automatically retry. You can also
                          // return a specific retry interval here.
                      }
                  }

                });

            } else {
                setError("Geolocation is not supported by your browser");
            }

        } catch (error) {
            console.error("Error fetching podium data:", error);

        } finally {
          setIsSubmitting(false); // Re-enable input and button after request completes
        }
    }
  };


  const handleCardClick = (cardData) => {
    setSelectedCard(cardData);
    setIsModalOpen(true);
  };


  const handleCloseModal = () => setIsModalOpen(false);


  const handleReroll = () => {
    setStartIndex((prevIndex) => (prevIndex + itemsPerPage) % Object.keys(podiumData).length);

  };

 
  useEffect(() => {
    if (showPodium) {
      setTimeout(() => setAnimateCards(true), 100);
    }
  }, [showPodium]);


  return (
    <div className="podium-container">
      <div className="podium-wrapper">
        <p>{streamData}</p>
        <div className="input-wrapper">
          <input
            type="text"
            className="input-field"
            placeholder="Type something and press Enter..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            autoFocus
            disabled={isSubmitting}
          />
        </div>

        <p>{error}</p>

        {showPodium && podiumData && (
          <div className={`podium-grid ${animateCards ? "animate" : ""}`}>
            {Object.entries(podiumData)
              .slice(startIndex, startIndex + itemsPerPage)
              .map(([key, value], index) => (

              <div
                key={key}
                className={`podium-card ${index === 0 ? "first-place" : index === 1 ? "second-place" : "third-place"}`}
                onClick={() => handleCardClick({
                  title: value.name,
                  rating: value.rating,
                  image: value.photo, // Placeholder, replace with API data if available
                  googleMaps: value.maps_uri,
                  delivery: value.delivery,
                })}
              >
                <div className="card-image">
                  <img src={value.photo} alt={value.name} />
                </div>
                <div className="card-content">{value.name}</div>
              </div>
            ))}
          </div>
        )}

        {showPodium && (
          <div>
          <button className="reroll-button" onClick={handleReroll}>
             Show next 
          </button>
          <button className="reroll-button" onClick={handleLogout}>
          🔒 Logout
          </button>
          </div>
        )}

        {/* Modal Window */}
        {isModalOpen && selectedCard && (
          <div className="modal-overlay">
            <div className="modal-content">
              <button className="modal-close-btn" onClick={handleCloseModal}>
                &times;
              </button>
              <div className="modal-card">
                <div className="modal-card-image">
                  <img src={selectedCard?.image} alt={selectedCard?.title} />
                </div>
                <div className="modal-card-text">{selectedCard?.title}</div>
                <div className="modal-details">
                  <div className="modal-detail">
                    <strong></strong> <a href={selectedCard?.googleMaps} target="_blank" rel="noopener noreferrer">View on Google Maps</a>
                  </div>
                  <div className="modal-detail">
                    <strong>Delivery:</strong> {selectedCard?.delivery}
                  </div>
                  <div className="modal-detail">
                    <strong>Rating:</strong> {selectedCard?.rating}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      <h3>Instructions</h3>

      {showPodium && (
          <div>
          <p>Click on a card to check out the restaurant. <br/>
          You can tell the robot what you like and dislike.</p>

          </div>
      )}
          <p>Remember to allow location in browser. <br/>
             Otherwise the results can be quite far away.</p>

      
        <p>Tips</p>
        <li>Use terms containing foods</li>
        <li>Avoid gibberish</li>
        <li>Be concise</li>
      <div>
        <p><Link to="/">Home</Link></p>
      </div>
    </div>
  );
};

export default PodiumUI;

