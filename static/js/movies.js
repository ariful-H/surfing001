// Movies Page JavaScript
document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const videoGrid = document.getElementById('video-grid');
    const loadingSpinner = document.getElementById('loading-spinner');
    const filterChips = document.querySelectorAll('.chip');

    // State
    let nextPageToken = '';
    let currentQuery = '';
    let isLoading = false;
    let selectedCategory = 'All';

    // Initialize
    init();

    async function init() {
        setupEventListeners();
        await loadInitialVideos();
    }
    
    function setupEventListeners() {
        // Search form submission
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const query = searchInput.value.trim();
            if (query) {
                searchVideos(query);
        }
        });

        // Filter chips
        filterChips.forEach(chip => {
            chip.addEventListener('click', () => {
                filterChips.forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                selectedCategory = chip.textContent;
                searchVideos(selectedCategory === 'All' ? '' : selectedCategory);
            });
        });

        // Infinite scroll
        window.addEventListener('scroll', () => {
            if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 1000) {
                if (!isLoading && nextPageToken) {
                    loadMoreVideos();
                }
                }
            });
    }

    async function searchVideos(query) {
        try {
            isLoading = true;
            currentQuery = query;
            nextPageToken = '';
            videoGrid.innerHTML = '';
            showLoading();

            const response = await fetch(`/api/youtube/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.items && data.items.length > 0) {
                nextPageToken = data.nextPageToken || '';
                displayVideos(data.items);
            } else {
                videoGrid.innerHTML = '<div class="no-results">No videos found</div>';
            }
        } catch (error) {
            console.error('Error searching videos:', error);
            videoGrid.innerHTML = '<div class="error">Error loading videos</div>';
        } finally {
            hideLoading();
            isLoading = false;
                    }
    }

    async function loadInitialVideos() {
        try {
            showLoading();
            const response = await fetch('/api/youtube/trending');
            const data = await response.json();

            if (data.items && data.items.length > 0) {
                nextPageToken = data.nextPageToken || '';
                displayVideos(data.items);
            }
        } catch (error) {
            console.error('Error loading initial videos:', error);
        } finally {
            hideLoading();
        }
    }

    async function loadMoreVideos() {
        if (!nextPageToken || isLoading) return;

        try {
            isLoading = true;
            showLoading();

            const endpoint = currentQuery ? 
                `/api/youtube/search?q=${encodeURIComponent(currentQuery)}&pageToken=${nextPageToken}` :
                `/api/youtube/trending?pageToken=${nextPageToken}`;

            const response = await fetch(endpoint);
                const data = await response.json();

            if (data.items && data.items.length > 0) {
                nextPageToken = data.nextPageToken || '';
                displayVideos(data.items, true);
            }
        } catch (error) {
            console.error('Error loading more videos:', error);
        } finally {
            hideLoading();
            isLoading = false;
        }
    }

    function displayVideos(videos, append = false) {
        const videoElements = videos.map(video => {
            const snippet = video.snippet;
            const videoId = video.id.videoId || video.id;
            
            return `
                <div class="video-card" data-video-id="${videoId}">
                    <div class="thumbnail-container">
                        <img class="video-thumbnail" src="${snippet.thumbnails.high.url}" alt="${snippet.title}">
                        <div class="video-duration"></div>
                    </div>
                    <div class="video-info">
                        <div class="video-details">
                            <img class="channel-avatar" src="/api/youtube/channel/${snippet.channelId}/avatar" alt="${snippet.channelTitle}">
                            <div class="video-text">
                                <h3 class="video-title">${snippet.title}</h3>
                                <div class="channel-name">${snippet.channelTitle}</div>
                                <div class="video-stats">
                                    <span class="views">Loading views...</span>
                                    <span class="dot">•</span>
                                    <span class="published">${formatPublishedDate(snippet.publishedAt)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        if (append) {
            videoGrid.insertAdjacentHTML('beforeend', videoElements);
        } else {
            videoGrid.innerHTML = videoElements;
        }

        // Load video statistics
        videos.forEach(video => {
            const videoId = video.id.videoId || video.id;
            loadVideoStats(videoId);
            });
            
        // Add click handlers
        document.querySelectorAll('.video-card').forEach(card => {
            card.addEventListener('click', () => {
                const videoId = card.dataset.videoId;
                window.location.href = `/watch?v=${videoId}`;
            });
        });
    }
    
    async function loadVideoStats(videoId) {
        try {
            const response = await fetch(`/api/youtube/videos/${videoId}/stats`);
                const data = await response.json();
            
            const card = document.querySelector(`.video-card[data-video-id="${videoId}"]`);
            if (card) {
                const viewsElement = card.querySelector('.views');
                const durationElement = card.querySelector('.video-duration');
                
                if (viewsElement) {
                    viewsElement.textContent = formatViewCount(data.statistics.viewCount);
                }
                if (durationElement) {
                    durationElement.textContent = formatDuration(data.contentDetails.duration);
                }
            }
        } catch (error) {
            console.error('Error loading video stats:', error);
        }
    }
    
    function formatViewCount(views) {
        if (views >= 1000000) {
            return `${Math.floor(views / 1000000)}M views`;
        } else if (views >= 1000) {
            return `${Math.floor(views / 1000)}K views`;
        }
        return `${views} views`;
    }

    function formatPublishedDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        const months = Math.floor(days / 30);
        const years = Math.floor(days / 365);

        if (years > 0) return `${years} year${years === 1 ? '' : 's'} ago`;
        if (months > 0) return `${months} month${months === 1 ? '' : 's'} ago`;
        if (days > 0) return `${days} day${days === 1 ? '' : 's'} ago`;
        if (hours > 0) return `${hours} hour${hours === 1 ? '' : 's'} ago`;
        if (minutes > 0) return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
        return 'Just now';
    }

    function formatDuration(duration) {
        const match = duration.match(/PT(\d+H)?(\d+M)?(\d+S)?/);
        
        const hours = (match[1] || '').replace('H', '');
        const minutes = (match[2] || '').replace('M', '');
        const seconds = (match[3] || '').replace('S', '');

        let result = '';
        
        if (hours) {
            result += `${hours}:`;
            result += `${minutes.padStart(2, '0')}:`;
        } else if (minutes) {
            result += `${minutes}:`;
        } else {
            result += '0:';
            }
        
        result += seconds.padStart(2, '0');
        
        return result;
    }

    function showLoading() {
        loadingSpinner.classList.add('active');
                }

    function hideLoading() {
        loadingSpinner.classList.remove('active');
    }
});