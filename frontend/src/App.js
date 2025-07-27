import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import './App.css';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth setup
const setupAuth = (username, password) => {
  const token = btoa(`${username}:${password}`);
  axios.defaults.headers.common['Authorization'] = `Basic ${token}`;
};

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [posts, setPosts] = useState([]);
  const [selectedPlatform, setSelectedPlatform] = useState('instagram');
  const [newUsername, setNewUsername] = useState('');
  const [postForm, setPostForm] = useState({
    title: '',
    platform: 'instagram',
    post_id: '',
    post_date: ''
  });
  const [analysis, setAnalysis] = useState(null);
  const [weeklyReport, setWeeklyReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState({ show: false, message: '', type: 'success' });

  // Notification system
  const showNotification = (message, type = 'success') => {
    setNotification({ show: true, message, type });
    setTimeout(() => {
      setNotification({ show: false, message: '', type: 'success' });
    }, 4000);
  };

  // Login Component with modern design
  const LoginForm = () => {
    const [credentials, setCredentials] = useState({ username: '', password: '' });
    const [loginLoading, setLoginLoading] = useState(false);

    const handleLogin = async (e) => {
      e.preventDefault();
      setLoginLoading(true);
      try {
        setupAuth(credentials.username, credentials.password);
        await axios.post(`${API}/login`);
        setIsLoggedIn(true);
        showNotification('Başarıyla giriş yapıldı! Hoş geldiniz.', 'success');
        fetchUsers();
        fetchPosts();
      } catch (error) {
        showNotification('Giriş başarısız! Kullanıcı adı: admin, Şifre: admin123', 'error');
      }
      setLoginLoading(false);
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center p-4">
        <div className="absolute inset-0 bg-black opacity-20"></div>
        <div className="relative z-10 bg-white/10 backdrop-blur-lg p-8 rounded-2xl shadow-2xl w-full max-w-md border border-white/20">
          <div className="text-center mb-8">
            <div className="mx-auto w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mb-6">
              <span className="text-3xl">📊</span>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">
              Sosyal Medya Takip
            </h1>
            <p className="text-gray-300 text-sm">
              Etkileşim analizi ve raporlama sistemi
            </p>
          </div>
          
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Kullanıcı Adı
              </label>
              <input
                type="text"
                value={credentials.username}
                onChange={(e) => setCredentials({...credentials, username: e.target.value})}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white placeholder-gray-400"
                placeholder="Kullanıcı adınızı girin"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Şifre
              </label>
              <input
                type="password"
                value={credentials.password}
                onChange={(e) => setCredentials({...credentials, password: e.target.value})}
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white placeholder-gray-400"
                placeholder="Şifrenizi girin"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loginLoading}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-6 rounded-lg hover:from-blue-700 hover:to-purple-700 transition duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {loginLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Giriş yapılıyor...
                </>
              ) : (
                'Giriş Yap'
              )}
            </button>
          </form>
          
          <div className="mt-6 p-4 bg-blue-500/20 rounded-lg border border-blue-400/30">
            <p className="text-sm text-blue-200 text-center">
              <span className="font-medium">Demo Bilgileri:</span><br />
              Kullanıcı Adı: <span className="font-mono">admin</span><br />
              Şifre: <span className="font-mono">admin123</span>
            </p>
          </div>
        </div>
      </div>
    );
  };

  // File Upload Component
  const FileUploader = ({ onUpload, acceptedTypes, text }) => {
    const { getRootProps, getInputProps, isDragActive } = useDropzone({
      accept: acceptedTypes,
      onDrop: (files) => onUpload(files[0])
    });

    return (
      <div
        {...getRootProps()}
        className={`border-2 border-dashed p-6 rounded-lg cursor-pointer transition-colors ${
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
        }`}
      >
        <input {...getInputProps()} />
        <div className="text-center">
          <div className="text-4xl mb-4">📁</div>
          <p className="text-lg font-medium">{text}</p>
          <p className="text-sm text-gray-500 mt-2">
            CSV veya Excel dosyası sürükleyip bırakın ya da tıklayın
          </p>
        </div>
      </div>
    );
  };

  // Fetch functions
  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
    } catch (error) {
      console.error('Kullanıcılar yüklenemedi:', error);
    }
  };

  const fetchPosts = async () => {
    try {
      const response = await axios.get(`${API}/posts`);
      setPosts(response.data);
    } catch (error) {
      console.error('Gönderiler yüklenemedi:', error);
    }
  };

  const fetchWeeklyReport = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/reports/weekly`);
      setWeeklyReport(response.data);
    } catch (error) {
      console.error('Haftalık rapor yüklenemedi:', error);
    }
    setLoading(false);
  };

  // Upload handlers
  const handleUserUpload = async (file) => {
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('platform', selectedPlatform);

    try {
      const response = await axios.post(`${API}/users/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      alert(response.data.message);
      fetchUsers();
    } catch (error) {
      alert('Dosya yükleme hatası: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const handleAddUser = async (e) => {
    e.preventDefault();
    if (!newUsername.trim()) return;

    try {
      await axios.post(`${API}/users/add`, {
        username: newUsername.trim(),
        platform: selectedPlatform
      });
      setNewUsername('');
      alert('Kullanıcı başarıyla eklendi!');
      fetchUsers();
    } catch (error) {
      alert('Kullanıcı ekleme hatası: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleCreatePost = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/posts`, {
        ...postForm,
        post_date: new Date(postForm.post_date).toISOString()
      });
      setPostForm({ title: '', platform: 'instagram', post_id: '', post_date: '' });
      alert('Gönderi başarıyla eklendi!');
      fetchPosts();
    } catch (error) {
      alert('Gönderi ekleme hatası: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEngagementUpload = async (postId, file) => {
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('post_id', postId);

    try {
      const response = await axios.post(`${API}/engagements/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      alert(response.data.message);
    } catch (error) {
      alert('Etkileşim yükleme hatası: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const handleAnalyzePost = async (postId) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/engagements/analysis/${postId}`);
      setAnalysis(response.data);
    } catch (error) {
      alert('Analiz hatası: ' + (error.response?.data?.detail || error.message));
    }
    setLoading(false);
  };

  const deleteUser = async (userId) => {
    if (window.confirm('Bu kullanıcıyı silmek istediğinizden emin misiniz?')) {
      try {
        await axios.delete(`${API}/users/${userId}`);
        alert('Kullanıcı silindi!');
        fetchUsers();
      } catch (error) {
        alert('Silme hatası: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  // Render Analysis Charts
  const renderAnalysisCharts = () => {
    if (!analysis) return null;

    const pieData = {
      labels: ['Etkileşim Yapanlar', 'Etkileşim Yapmayanlar'],
      datasets: [{
        data: [analysis.total_engaged, analysis.total_management - analysis.total_engaged],
        backgroundColor: ['#10B981', '#EF4444'],
        borderWidth: 0
      }]
    };

    return (
      <div className="bg-white p-6 rounded-lg shadow-lg">
        <h3 className="text-xl font-bold mb-4">{analysis.post_title} - Analiz Sonuçları</h3>
        
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <div className="w-64 h-64 mx-auto">
              <Pie data={pieData} options={{ maintainAspectRatio: false }} />
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded">
              <h4 className="font-semibold text-lg">Özet İstatistikler</h4>
              <div className="mt-2 space-y-2">
                <p><span className="font-medium">Platform:</span> {analysis.platform.toUpperCase()}</p>
                <p><span className="font-medium">Toplam Yönetici:</span> {analysis.total_management}</p>
                <p><span className="font-medium">Etkileşim Yapan:</span> {analysis.total_engaged}</p>
                <p><span className="font-medium">Etkileşim Oranı:</span> {analysis.engagement_percentage}%</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mt-6">
          <div>
            <h4 className="font-semibold text-green-600 mb-2">Etkileşim Yapanlar ({analysis.engaged_users.length})</h4>
            <div className="bg-green-50 p-4 rounded max-h-40 overflow-y-auto">
              {analysis.engaged_users.map((user, idx) => (
                <span key={idx} className="inline-block bg-green-200 text-green-800 px-2 py-1 rounded text-sm mr-2 mb-2">
                  @{user}
                </span>
              ))}
            </div>
          </div>
          
          <div>
            <h4 className="font-semibold text-red-600 mb-2">Etkileşim Yapmayanlar ({analysis.not_engaged_users.length})</h4>
            <div className="bg-red-50 p-4 rounded max-h-40 overflow-y-auto">
              {analysis.not_engaged_users.map((user, idx) => (
                <span key={idx} className="inline-block bg-red-200 text-red-800 px-2 py-1 rounded text-sm mr-2 mb-2">
                  @{user}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (!isLoggedIn) {
    return <LoginForm />;
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-800">
              Sosyal Medya Etkileşim Takip Sistemi
            </h1>
            <button
              onClick={() => setIsLoggedIn(false)}
              className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
            >
              Çıkış Yap
            </button>
          </div>
          
          {/* Navigation */}
          <nav className="mt-4">
            <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
              {[
                { id: 'users', label: 'Kullanıcı Yönetimi', icon: '👥' },
                { id: 'posts', label: 'Gönderi Yönetimi', icon: '📝' },
                { id: 'analysis', label: 'Etkileşim Analizi', icon: '📊' },
                { id: 'reports', label: 'Haftalık Raporlar', icon: '📈' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex-1 flex items-center justify-center px-4 py-2 rounded-md transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </div>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* User Management Tab */}
        {activeTab === 'users' && (
          <div className="space-y-8">
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-bold mb-6">Kullanıcı Yönetimi</h2>
              
              {/* Platform Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">Platform Seçin</label>
                <div className="flex space-x-4">
                  <button
                    onClick={() => setSelectedPlatform('instagram')}
                    className={`px-4 py-2 rounded ${selectedPlatform === 'instagram' ? 'bg-pink-500 text-white' : 'bg-gray-200'}`}
                  >
                    📸 Instagram
                  </button>
                  <button
                    onClick={() => setSelectedPlatform('x')}
                    className={`px-4 py-2 rounded ${selectedPlatform === 'x' ? 'bg-black text-white' : 'bg-gray-200'}`}
                  >
                    𝕏 Twitter/X
                  </button>
                </div>
              </div>

              {/* File Upload */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-4">Toplu Kullanıcı Yükleme</h3>
                <FileUploader
                  onUpload={handleUserUpload}
                  acceptedTypes={{
                    'text/csv': ['.csv'],
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
                    'application/vnd.ms-excel': ['.xls']
                  }}
                  text={`${selectedPlatform.toUpperCase()} kullanıcı adları dosyası yükleyin`}
                />
              </div>

              {/* Manual User Addition */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-4">Tek Kullanıcı Ekleme</h3>
                <form onSubmit={handleAddUser} className="flex gap-4">
                  <input
                    type="text"
                    value={newUsername}
                    onChange={(e) => setNewUsername(e.target.value)}
                    placeholder="Kullanıcı adını girin (@ olmadan)"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    type="submit"
                    className="bg-green-500 text-white px-6 py-2 rounded-md hover:bg-green-600"
                  >
                    Ekle
                  </button>
                </form>
              </div>
            </div>

            {/* Users List */}
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h3 className="text-xl font-bold mb-4">Kullanıcı Listesi</h3>
              <div className="grid gap-4">
                {['instagram', 'x'].map(platform => {
                  const platformUsers = users.filter(u => u.platform === platform);
                  return (
                    <div key={platform} className="border rounded-lg p-4">
                      <h4 className="font-semibold text-lg mb-3 flex items-center">
                        {platform === 'instagram' ? '📸 Instagram' : '𝕏 Twitter/X'}
                        <span className="ml-2 text-sm bg-gray-200 px-2 py-1 rounded">
                          {platformUsers.length} kullanıcı
                        </span>
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-2 max-h-40 overflow-y-auto">
                        {platformUsers.map(user => (
                          <div key={user.id} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                            <span>@{user.username}</span>
                            <button
                              onClick={() => deleteUser(user.id)}
                              className="text-red-500 hover:text-red-700 text-sm"
                            >
                              Sil
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Posts Management Tab */}
        {activeTab === 'posts' && (
          <div className="space-y-8">
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-bold mb-6">Gönderi Yönetimi</h2>
              
              <form onSubmit={handleCreatePost} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Gönderi Başlığı</label>
                  <input
                    type="text"
                    value={postForm.title}
                    onChange={(e) => setPostForm({...postForm, title: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Platform</label>
                  <select
                    value={postForm.platform}
                    onChange={(e) => setPostForm({...postForm, platform: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="instagram">Instagram</option>
                    <option value="x">Twitter/X</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Gönderi ID</label>
                  <input
                    type="text"
                    value={postForm.post_id}
                    onChange={(e) => setPostForm({...postForm, post_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Gönderi Tarihi</label>
                  <input
                    type="datetime-local"
                    value={postForm.post_date}
                    onChange={(e) => setPostForm({...postForm, post_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    required
                  />
                </div>
                
                <button
                  type="submit"
                  className="bg-blue-500 text-white px-6 py-2 rounded-md hover:bg-blue-600"
                >
                  Gönderi Ekle
                </button>
              </form>
            </div>

            {/* Posts List */}
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h3 className="text-xl font-bold mb-4">Gönderiler</h3>
              <div className="space-y-4">
                {posts.map(post => (
                  <div key={post.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-semibold">{post.title}</h4>
                        <p className="text-sm text-gray-600">
                          {post.platform.toUpperCase()} • {new Date(post.post_date).toLocaleDateString('tr-TR')}
                        </p>
                      </div>
                      <div className="space-x-2">
                        <FileUploader
                          onUpload={(file) => handleEngagementUpload(post.id, file)}
                          acceptedTypes={{
                            'text/csv': ['.csv'],
                            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
                          }}
                          text="Beğeni Verilerini Yükle"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Analysis Tab */}
        {activeTab === 'analysis' && (
          <div className="space-y-8">
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h2 className="text-2xl font-bold mb-6">Etkileşim Analizi</h2>
              
              <div className="grid gap-4">
                {posts.map(post => (
                  <div key={post.id} className="border rounded-lg p-4 flex justify-between items-center">
                    <div>
                      <h4 className="font-semibold">{post.title}</h4>
                      <p className="text-sm text-gray-600">{post.platform.toUpperCase()}</p>
                    </div>
                    <button
                      onClick={() => handleAnalyzePost(post.id)}
                      className="bg-purple-500 text-white px-4 py-2 rounded-md hover:bg-purple-600"
                      disabled={loading}
                    >
                      {loading ? 'Analiz Ediliyor...' : 'Analiz Et'}
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {analysis && renderAnalysisCharts()}
          </div>
        )}

        {/* Weekly Reports Tab */}
        {activeTab === 'reports' && (
          <div className="space-y-8">
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold">Haftalık Raporlar</h2>
                <button
                  onClick={fetchWeeklyReport}
                  className="bg-green-500 text-white px-4 py-2 rounded-md hover:bg-green-600"
                  disabled={loading}
                >
                  {loading ? 'Yükleniyor...' : 'Rapor Oluştur'}
                </button>
              </div>

              {weeklyReport && (
                <div>
                  <div className="mb-6 grid grid-cols-3 gap-4">
                    <div className="bg-blue-50 p-4 rounded text-center">
                      <div className="text-2xl font-bold text-blue-600">{weeklyReport.summary.total_users}</div>
                      <div className="text-sm text-gray-600">Toplam Kullanıcı</div>
                    </div>
                    <div className="bg-green-50 p-4 rounded text-center">
                      <div className="text-2xl font-bold text-green-600">{weeklyReport.summary.active_users}</div>
                      <div className="text-sm text-gray-600">Aktif Kullanıcı</div>
                    </div>
                    <div className="bg-purple-50 p-4 rounded text-center">
                      <div className="text-2xl font-bold text-purple-600">{weeklyReport.summary.total_posts}</div>
                      <div className="text-sm text-gray-600">Toplam Gönderi</div>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse border">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="border p-3 text-left">Kullanıcı Adı</th>
                          <th className="border p-3 text-left">Platform</th>
                          <th className="border p-3 text-center">Etkileşim Yapılan</th>
                          <th className="border p-3 text-center">Toplam Gönderi</th>
                          <th className="border p-3 text-center">Etkileşim Oranı</th>
                        </tr>
                      </thead>
                      <tbody>
                        {weeklyReport.users.map((user, idx) => (
                          <tr key={idx} className={user.engagement_rate === 0 ? 'bg-red-50' : ''}>
                            <td className="border p-3">@{user.username}</td>
                            <td className="border p-3">
                              {user.platform === 'instagram' ? '📸 Instagram' : '𝕏 Twitter/X'}
                            </td>
                            <td className="border p-3 text-center">{user.engaged_posts}</td>
                            <td className="border p-3 text-center">{user.total_posts}</td>
                            <td className="border p-3 text-center">
                              <span className={`px-2 py-1 rounded text-sm ${
                                user.engagement_rate >= 80 ? 'bg-green-200 text-green-800' :
                                user.engagement_rate >= 50 ? 'bg-yellow-200 text-yellow-800' :
                                'bg-red-200 text-red-800'
                              }`}>
                                {user.engagement_rate}%
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4">İşlem yapılıyor...</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;