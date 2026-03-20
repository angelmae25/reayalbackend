// =============================================================================
// lib/services/data_service.dart
//
// All services call the Flask API.
// JWT token comes from AuthService (stored in SharedPreferences after login).
// SQLite (sqflite) is used as a local cache so the app works offline.
//
// Android Emulator  → 10.0.2.2:5000
// Physical device   → your computer's WiFi IP e.g. 192.168.1.5:5000
// =============================================================================

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart' as p;
import '../models/news_model.dart';
import '../models/models.dart';
import '../models/user_model.dart';
import 'auth_service.dart';

// ── Base URL ─────────────────────────────────────────────────────────────────
// Android Emulator:
const String _base = 'http://10.0.2.2:5000/api/mobile';
// Physical device — replace with your PC's LAN IP:
// const String _base = 'http://192.168.1.xxx:5000/api/mobile';

// ── JWT Auth header ───────────────────────────────────────────────────────────
Future<Map<String, String>> _headers() async {
  final token = await AuthService.instance.getToken();
  return {
    'Content-Type':  'application/json',
    'Authorization': 'Bearer ${token ?? ''}',
  };
}

// =============================================================================
// LOCAL DATABASE (SQLite via sqflite)
// Caches API responses so the app loads instantly and works offline.
// =============================================================================
class LocalDb {
  LocalDb._();
  static final LocalDb instance = LocalDb._();
  Database? _db;

  Future<Database> get db async {
    _db ??= await _open();
    return _db!;
  }

  Future<Database> _open() async {
    final dbPath = await getDatabasesPath();
    return openDatabase(
      p.join(dbPath, 'scholife_cache.db'),
      version: 1,
      onCreate: (db, _) async {
        await db.execute('''
          CREATE TABLE news_cache (
            id TEXT PRIMARY KEY,
            json TEXT NOT NULL,
            cached_at INTEGER NOT NULL
          )
        ''');
        await db.execute('''
          CREATE TABLE events_cache (
            id TEXT PRIMARY KEY,
            json TEXT NOT NULL,
            cached_at INTEGER NOT NULL
          )
        ''');
        await db.execute('''
          CREATE TABLE clubs_cache (
            id TEXT PRIMARY KEY,
            json TEXT NOT NULL,
            cached_at INTEGER NOT NULL
          )
        ''');
        await db.execute('''
          CREATE TABLE marketplace_cache (
            id TEXT PRIMARY KEY,
            json TEXT NOT NULL,
            cached_at INTEGER NOT NULL
          )
        ''');
        await db.execute('''
          CREATE TABLE lost_found_cache (
            id TEXT PRIMARY KEY,
            json TEXT NOT NULL,
            cached_at INTEGER NOT NULL
          )
        ''');
        await db.execute('''
          CREATE TABLE leaderboard_cache (
            id TEXT PRIMARY KEY,
            json TEXT NOT NULL,
            cached_at INTEGER NOT NULL
          )
        ''');
      },
    );
  }

  // ── Generic cache helpers ─────────────────────────────────────────────────

  Future<void> cacheList(String table, List<Map<String, dynamic>> items) async {
    final database = await db;
    final batch    = database.batch();
    batch.delete(table);  // clear old cache
    final now = DateTime.now().millisecondsSinceEpoch;
    for (final item in items) {
      batch.insert(table, {
        'id':        item['id']?.toString() ?? '',
        'json':      jsonEncode(item),
        'cached_at': now,
      }, conflictAlgorithm: ConflictAlgorithm.replace);
    }
    await batch.commit(noResult: true);
  }

  Future<List<Map<String, dynamic>>> getCache(String table) async {
    final database = await db;
    final rows     = await database.query(table, orderBy: 'cached_at ASC');
    return rows.map((r) => jsonDecode(r['json'] as String) as Map<String, dynamic>).toList();
  }

  Future<bool> isCacheFresh(String table, {int maxAgeMinutes = 10}) async {
    final database = await db;
    final rows     = await database.query(table, orderBy: 'cached_at DESC', limit: 1);
    if (rows.isEmpty) return false;
    final cachedAt = rows.first['cached_at'] as int;
    final age      = DateTime.now().millisecondsSinceEpoch - cachedAt;
    return age < maxAgeMinutes * 60 * 1000;
  }
}

// =============================================================================
// NEWS SERVICE
// =============================================================================
class NewsService {
  NewsService._();
  static final NewsService instance = NewsService._();

  Future<List<NewsModel>> fetchAll({String category = 'all'}) async {
    try {
      final res = await http.get(
        Uri.parse('$_base/news/?category=$category'),
        headers: await _headers(),
      ).timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final list = (jsonDecode(res.body) as List).cast<Map<String, dynamic>>();
        // Save to local cache
        await LocalDb.instance.cacheList('news_cache', list);
        return list.map(NewsModel.fromJson).toList();
      }
    } catch (_) {
      // Network failed → fall back to cache
    }
    // Offline fallback
    final cached = await LocalDb.instance.getCache('news_cache');
    if (cached.isNotEmpty) return cached.map(NewsModel.fromJson).toList();
    return NewsModel.mockList;
  }

  Future<List<NewsModel>> fetchByCategory(NewsCategory category) =>
      fetchAll(category: category.name);
}

// =============================================================================
// EVENT SERVICE
// =============================================================================
class EventService {
  EventService._();
  static final EventService instance = EventService._();

  Future<List<EventModel>> fetchAll() async {
    try {
      final res = await http.get(
        Uri.parse('$_base/events/'),
        headers: await _headers(),
      ).timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final list = (jsonDecode(res.body) as List).cast<Map<String, dynamic>>();
        await LocalDb.instance.cacheList('events_cache', list);
        return list.map(EventModel.fromJson).toList();
      }
    } catch (_) {}
    final cached = await LocalDb.instance.getCache('events_cache');
    if (cached.isNotEmpty) return cached.map(EventModel.fromJson).toList();
    return EventModel.mockList;
  }
}

// =============================================================================
// CLUB SERVICE
// =============================================================================
class ClubService {
  ClubService._();
  static final ClubService instance = ClubService._();

  Future<List<ClubModel>> fetchAll() async {
    try {
      final res = await http.get(
        Uri.parse('$_base/clubs/'),
        headers: await _headers(),
      ).timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final list = (jsonDecode(res.body) as List).cast<Map<String, dynamic>>();
        await LocalDb.instance.cacheList('clubs_cache', list);
        return list.map((j) => ClubModel.fromApi(j)).toList();
      }
    } catch (_) {}
    final cached = await LocalDb.instance.getCache('clubs_cache');
    if (cached.isNotEmpty) return cached.map((j) => ClubModel.fromApi(j)).toList();
    return ClubModel.mockList;
  }

  Future<void> toggleMembership(String clubId, bool join) async {
    final endpoint = join ? 'join' : 'leave';
    try {
      await http.post(
        Uri.parse('$_base/clubs/$clubId/$endpoint'),
        headers: await _headers(),
      );
    } catch (_) {
      // Optimistic UI — ignore network error, local state already updated
    }
  }
}

// =============================================================================
// LEADERBOARD SERVICE
// =============================================================================
class LeaderboardService {
  LeaderboardService._();
  static final LeaderboardService instance = LeaderboardService._();

  Future<List<LeaderboardEntryModel>> fetchAll() async {
    try {
      final res = await http.get(
        Uri.parse('$_base/leaderboard/'),
        headers: await _headers(),
      ).timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final list = (jsonDecode(res.body) as List).cast<Map<String, dynamic>>();
        await LocalDb.instance.cacheList('leaderboard_cache', list);
        return list
            .asMap()
            .entries
            .map((e) => LeaderboardEntryModel.fromJson({
                  ...e.value,
                  'rank': (e.value['rank'] as int?) ?? e.key + 1,
                }))
            .toList();
      }
    } catch (_) {}
    final cached = await LocalDb.instance.getCache('leaderboard_cache');
    if (cached.isNotEmpty) {
      return cached
          .asMap()
          .entries
          .map((e) => LeaderboardEntryModel.fromJson({...e.value, 'rank': e.key + 1}))
          .toList();
    }
    return LeaderboardEntryModel.mockList;
  }
}

// =============================================================================
// USER SERVICE
// =============================================================================
class UserService {
  UserService._();
  static final UserService instance = UserService._();

  Future<UserModel> fetchProfile(String userId) async {
    try {
      final res = await http.get(
        Uri.parse('$_base/students/profile'),
        headers: await _headers(),
      ).timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        return UserModel.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
      }
    } catch (_) {}
    return AuthService.instance.fetchMe();
  }

  Future<UserModel> updateProfile(UserModel updated) async {
    final res = await http.put(
      Uri.parse('$_base/students/profile'),
      headers: await _headers(),
      body: jsonEncode({
        'contact':    updated.phone,
        'avatar_url': updated.avatarUrl,
      }),
    );
    if (res.statusCode == 200) {
      return UserModel.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
    }
    throw Exception('Failed to update profile.');
  }
}

// =============================================================================
// MARKETPLACE SERVICE
// =============================================================================
class MarketplaceService {
  MarketplaceService._();
  static final MarketplaceService instance = MarketplaceService._();

  Future<List<MarketplaceItemModel>> fetchAll() async {
    try {
      final res = await http.get(
        Uri.parse('$_base/marketplace/'),
        headers: await _headers(),
      ).timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final list = (jsonDecode(res.body) as List).cast<Map<String, dynamic>>();
        await LocalDb.instance.cacheList('marketplace_cache', list);
        return list.map(MarketplaceItemModel.fromJson).toList();
      }
    } catch (_) {}
    final cached = await LocalDb.instance.getCache('marketplace_cache');
    if (cached.isNotEmpty) return cached.map(MarketplaceItemModel.fromJson).toList();
    return MarketplaceItemModel.mockList;
  }

  Future<List<MarketplaceItemModel>> search(String query) async {
    if (query.isEmpty) return fetchAll();
    try {
      final res = await http.get(
        Uri.parse('$_base/marketplace/?search=${Uri.encodeComponent(query)}'),
        headers: await _headers(),
      ).timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final list = (jsonDecode(res.body) as List).cast<Map<String, dynamic>>();
        return list.map(MarketplaceItemModel.fromJson).toList();
      }
    } catch (_) {}
    final all = await fetchAll();
    return all.where((i) => i.name.toLowerCase().contains(query.toLowerCase())).toList();
  }
}

// =============================================================================
// LOST & FOUND SERVICE
// =============================================================================
class LostFoundService {
  LostFoundService._();
  static final LostFoundService instance = LostFoundService._();

  Future<List<LostFoundModel>> fetchAll() async {
    try {
      final res = await http.get(
        Uri.parse('$_base/lost-found/'),
        headers: await _headers(),
      ).timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final list = (jsonDecode(res.body) as List).cast<Map<String, dynamic>>();
        await LocalDb.instance.cacheList('lost_found_cache', list);
        return list.map(LostFoundModel.fromJson).toList();
      }
    } catch (_) {}
    final cached = await LocalDb.instance.getCache('lost_found_cache');
    if (cached.isNotEmpty) return cached.map(LostFoundModel.fromJson).toList();
    return LostFoundModel.mockList;
  }

  Future<List<LostFoundModel>> fetchByStatus(LostFoundStatus status) async {
    final all = await fetchAll();
    return all.where((i) => i.status == status).toList();
  }
}

// =============================================================================
// CHAT SERVICE
// =============================================================================
class ChatService {
  ChatService._();
  static final ChatService instance = ChatService._();

  Future<List<ChatModel>> fetchConversations() async {
    try {
      final res = await http.get(
        Uri.parse('$_base/chat/conversations'),
        headers: await _headers(),
      ).timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final list = (jsonDecode(res.body) as List).cast<Map<String, dynamic>>();
        return list.map(_chatFromJson).toList();
      }
    } catch (_) {}
    return ChatModel.mockList;
  }

  Future<List<ChatMessageModel>> fetchMessages(String conversationId) async {
    try {
      final res = await http.get(
        Uri.parse('$_base/chat/conversations/$conversationId/messages'),
        headers: await _headers(),
      ).timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final list = (jsonDecode(res.body) as List).cast<Map<String, dynamic>>();
        return list.map(_msgFromJson).toList();
      }
    } catch (_) {}
    return ChatMessageModel.mockMessages;
  }

  Future<void> sendMessage(String conversationId, String text) async {
    try {
      await http.post(
        Uri.parse('$_base/chat/conversations/$conversationId/messages'),
        headers: await _headers(),
        body: jsonEncode({'text': text}),
      );
    } catch (_) {}
  }

  // ── JSON helpers ──────────────────────────────────────────────────────────
  ChatModel _chatFromJson(Map<String, dynamic> j) => ChatModel(
    id:             j['id']?.toString() ?? '',
    name:           j['name']            as String? ?? '',
    lastMessage:    j['last_message']    as String? ?? '',
    lastMessageAt:  DateTime.tryParse(j['last_message_at'] as String? ?? '') ?? DateTime.now(),
    unreadCount:    (j['unread_count']   as int?) ?? 0,
    isGroup:        (j['is_group']       as bool?) ?? false,
  );

  ChatMessageModel _msgFromJson(Map<String, dynamic> j) => ChatMessageModel(
    id:       j['id']?.toString() ?? '',
    text:     j['text']      as String? ?? '',
    senderId: j['sender_id'] as String? ?? '',
    sentAt:   DateTime.tryParse(j['sent_at'] as String? ?? '') ?? DateTime.now(),
    isMine:   (j['is_mine']  as bool?) ?? false,
  );
}
