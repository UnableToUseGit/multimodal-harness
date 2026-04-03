# ## 测试组一：URL；是否能下载视频；预期走 text route
# # lecture 18min
# video-atlas create --url https://www.youtube.com/watch?v=aircAruvnKk --output-dir local/outputs/test_video --structure-request "Structured into coarse-grained chapters"
# # commentary. 38min
video-atlas create --url https://www.youtube.com/watch?v=KMlYdvwiQ0Y --output-dir local/outputs/test_video --structure-request "结构化为5~8个章节"
# # video podcast 1:20:00
# video-atlas create --url https://www.youtube.com/watch?v=aR20FWCCjAs --output-dir local/outputs/test_video --structure-request "结构化为粗粒度的章节"

# ## 测试组二：URL；是否能下载视频；预期走 multi route
# # 脱口秀 1:55:00
# video-atlas create --url https://www.youtube.com/watch?v=ku7oevD0Kko --output-dir local/outputs/test_video 
# # 电影 1:20:00
# video-atlas create --url https://www.youtube.com/watch?v=-8-MbYZxpOo --output-dir local/outputs/test_video
# # Vlog 19:26
# video-atlas create --url https://www.youtube.com/watch?v=kaPgGH5HC0w --output-dir local/outputs/test_video

## 测试组三：PATH；预期走 text route
# video-atlas create \
#     --video-file local/inputs/case_011_explanatory_commentary_tech/全面解析世界模型.mp4 \
#     --subtitle-file local/inputs/case_011_explanatory_commentary_tech/subtitles.srt \
#     --structure-request "结构化为粗粒度的章节" \
#     --output-dir local/outputs/test_video

# video-atlas create \
#     --video-file local/inputs/case_013_explanatory_commentary_history/墨西哥是如何成为一个毒品国家的.mp4 \
#     --subtitle-file local/inputs/case_013_explanatory_commentary_history/subtitles.srt \
#     --structure-request "结构化为粗粒度的章节" \
#     --output-dir local/outputs/test_video

# video-atlas create \
#     --video-file local/inputs/case_003_podcast/鲁豫对话许知远：人生是一场持续的写作陈鲁豫·慢谈EP13【视频播客】.mp4 \
#     --subtitle-file local/inputs/case_003_podcast/subtitles.srt \
#     --structure-request "结构化为8～12个章节" \
#     --output-dir local/outputs/test_video

## 测试组四：PATH；预期走 multi route
# video-atlas create --video-file local/inputs/case_002_match_lol/lol.mp4 --subtitle-file local/inputs/case_002_match_lol/subtitles.srt --output-dir local/outputs/test_video
# video-atlas create --video-file local/inputs/case_009_vlog_paris/一个人在巴黎感知活在当下的意义.mp4 --subtitle-file local/inputs/case_009_vlog_paris/subtitles.srt --output-dir local/outputs/test_video

# ## 测试组五：小宇宙 URL；预期走 text route
# video-atlas create --url https://www.xiaoyuzhoufm.com/episode/66c3274033591c27be349dc7 --output-dir local/outputs/test_audio --structure-request "结构化为粗粒度的章节"
# video-atlas create --url https://www.xiaoyuzhoufm.com/episode/69cc1a0ce2c8be31550c581f --output-dir local/outputs/test_audio --structure-request "结构化为粗粒度的章节"
# video-atlas create --url https://www.xiaoyuzhoufm.com/episode/6709d53c81cdab3a936bd2e4 --output-dir local/outputs/test_audio --structure-request "结构化为粗粒度的章节"
# video-atlas create --url https://www.xiaoyuzhoufm.com/episode/69cbd0d3b977fb2c47c1ff80 --output-dir local/outputs/test_audio --structure-request "结构化为粗粒度的章节"