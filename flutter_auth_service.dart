// =============================================================================
// lib/services/auth_service.dart  (UPDATED — uses Flask JWT)
//
// Flutter now calls Flask on port 5000.
// Android Emulator  → 10.0.2.2:5000
// Physical device   → your computer's WiFi IP e.g. 192.168.1.5:5000
// =============================================================================

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user_model.dart';

class AuthService {
  AuthService._();
  static final AuthService instance = AuthService._();

  // ── Flask base URL ─────────────────────────────────────────────────────────
  static const String _base = 'http://10.0.2.2:5000/api/mobile';
  // Physical device:
  // static const String _base = 'http://192.168.1.xxx:5000/api/mobile';

  static const _kToken     = 'jwt_token';
  static const _kUserId    = 'user_id';
  static const _kUserEmail = 'user_email';
  static const _kUserName  = 'user_name';
  static const _kStudentId = 'student_id_key';

  // ── REGISTER → POST /auth/register ────────────────────────────────────────
  Future<UserModel> register({
    required String fullName,
    required String studentId,
    required String email,
    required String password,
  }) async {
    final res = await http.post(
      Uri.parse('$_base/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'full_name':  fullName,
        'student_id': studentId,
        'email':      email,
        'password':   password,
      }),
    );

    final body = jsonDecode(res.body) as Map<String, dynamic>;

    if (res.statusCode == 201) {
      // Account created but PENDING — just return a shell model.
      // The user will have to wait for admin approval before logging in.
      return UserModel(
        id:        body['id']?.toString() ?? '',
        fullName:  fullName,
        email:     email,
        studentId: studentId,
        course:    '',
        yearLevel: '1st Year',
      );
    }

    throw Exception(body['message'] ?? 'Registration failed.');
  }

  // ── SIGN IN → POST /auth/login ─────────────────────────────────────────────
  Future<UserModel> signIn({
    required String email,
    required String password,
  }) async {
    final res = await http.post(
      Uri.parse('$_base/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    final body = jsonDecode(res.body) as Map<String, dynamic>;

    if (res.statusCode == 200) {
      final token   = body['access_token'] as String;
      final student = body['student']      as Map<String, dynamic>;

      final user = UserModel.fromJson(student);

      await _saveSession(
        token:     token,
        id:        user.id,
        email:     user.email,
        fullName:  user.fullName,
        studentId: user.studentId,
      );

      return user;
    }

    throw Exception(body['message'] ?? 'Sign in failed. Please try again.');
  }

  // ── SIGN OUT ───────────────────────────────────────────────────────────────
  Future<void> signOut() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kToken);
    await prefs.remove(_kUserId);
    await prefs.remove(_kUserEmail);
    await prefs.remove(_kUserName);
    await prefs.remove(_kStudentId);
  }

  // ── AUTO-LOGIN ─────────────────────────────────────────────────────────────
  Future<UserModel?> tryAutoLogin() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(_kToken);
    final id    = prefs.getString(_kUserId);
    if (token == null || id == null) return null;

    return UserModel(
      id:        id,
      fullName:  prefs.getString(_kUserName)  ?? '',
      email:     prefs.getString(_kUserEmail) ?? '',
      studentId: prefs.getString(_kStudentId) ?? '',
      course:    '',
      yearLevel: '',
    );
  }

  // ── GET JWT TOKEN ─────────────────────────────────────────────────────────
  Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_kToken);
  }

  // ── FETCH ME (calls /students/profile) ────────────────────────────────────
  Future<UserModel> fetchMe() async {
    final user = await tryAutoLogin();
    if (user == null) throw Exception('Not logged in.');
    return user;
  }

  // ── Save session ───────────────────────────────────────────────────────────
  Future<void> _saveSession({
    required String token,
    required String id,
    required String email,
    required String fullName,
    required String studentId,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kToken,     token);
    await prefs.setString(_kUserId,    id);
    await prefs.setString(_kUserEmail, email);
    await prefs.setString(_kUserName,  fullName);
    await prefs.setString(_kStudentId, studentId);
  }
}
