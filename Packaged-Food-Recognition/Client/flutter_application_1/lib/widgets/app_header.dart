import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class AppHeader extends StatelessWidget {
  final VoidCallback? onBack;
  final bool showBack;
  final Widget? trailing;

  const AppHeader({
    super.key,
    this.onBack,
    this.showBack = true,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          if (showBack)
            GestureDetector(
              onTap: onBack ?? () => Navigator.of(context).maybePop(),
              child: Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: AppColors.chipUnselectedBg,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(
                  Icons.arrow_back_ios_new,
                  size: 18,
                  color: AppColors.textDark,
                ),
              ),
            )
          else
            const SizedBox(width: 44),

          // Custom trailing widget or standard Misbar Logo
          if (trailing != null)
            trailing!
          else
            SizedBox(
              height: 42,
              width: 95,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: Image.asset(
                  'assets/images/misbar_logo.png',
                  fit: BoxFit.cover,
                  alignment: const Alignment(0.0, -0.05),
                  errorBuilder: (_, __, ___) => const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.search, color: AppColors.primaryGreen, size: 20),
                      SizedBox(width: 4),
                      Text(
                        'Misbar',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: AppColors.primaryGreen,
                          fontSize: 16,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}