import json
import glob
import os
from pathlib import Path
import pandas as pd

# The 41 manual corrections mapping split_id -> corrected Vietnamese translation
manual_corrections = {
    "LORE_0000197": "Sinh vật đột biến cỡ lớn sinh sống sâu trong Hẻm núi Spirit, chiếc chuông cổ trên lưng chúng có thể phát nổ bằng sóng âm cực kỳ chí mạng khi rung lên.",
    "LORE_0000285": "Sinh vật đột biến cỡ lớn sinh sống sâu trong Hẻm núi Spirit, chiếc chuông cổ trên lưng chúng có thể phát nổ bằng sóng âm cực kỳ chí mạng khi rung lên.",
    
    "LORE_0000707": """Trích từ <i>Cây Búa Dị Giáo</i>
(Tập truyền đơn đưa ra một số quan điểm cực đoan, dường như phản ánh lý thuyết của một trường phái tư tưởng cực đoan.)

Phù thủy là gì? Và bản chất thực sự của nó là gì?
Sức mạnh Resonance do Resonators sử dụng được biết đến như một phước lành từ Sentinel Imperator. Những tín đồ trung thành của Giáo Đoàn được ban cho phước lành này khi tuân theo giáo lý, cho phép họ dẫn truyền sức mạnh thần thánh qua thân xác phàm trần. Tuy nhiên, phù thủy sinh ra từ những dục vọng hão huyền—những linh hồn bất tín, bị Leviathan dụ dỗ, lập giao ước để thực hành những nghệ thuật bị cấm. Bằng cách đó, chúng từ bỏ phước lành thần thánh được ban tặng từ khi sinh ra và vứt bỏ nhân tính, biến thành phù thủy tìm cách làm ô uế cõi trần bằng sức mạnh tà ác.
Đấng Tối Cao đã tạo dựng thế giới này, và tất cả những gì chúng ta trân quý đều bắt nguồn từ phước lành của Ngài. Thế nhưng, phù thủy, bị Kẻ Thù Vĩ Đại mê hoặc, đã biến những sáng tạo thần thánh ấy thành những thực thể ô uế, đáng hổ thẹn, tạo ra Resonance giả tạo với chúng. Dấu ấn của kẻ thù trên người những phù thủy này là bằng chứng cho tội lỗi của chúng. Với sự trợ giúp của Vessel of the Enemy, chúng thậm chí có thể biến thành Tacet Discords, đe dọa nghiêm trọng đến những tín đồ trung thành của Imperator.
<b>Hãy cảnh giác, bởi bất kỳ ai khao khát tự do và dục vọng trần tục đều có thể trở thành con cờ của Leviathan.</b>
Vì vậy, chúng ta phải thường xuyên thanh tẩy và trừ tà những linh hồn như vậy. Nếu để những kẻ dị giáo này phát triển không kiểm soát, sử dụng sức mạnh ô uế để làm nhơ nhuốc cõi trần, chúng chắc chắn sẽ mang Dark Tide đến với Rinascita. Bổn phận của Giáo Đoàn là dẫn dắt và cai quản chúng, đảm bảo chúng tuân theo ý chí thần thánh của Imperator. Nếu chúng từ chối gia nhập Giáo Đoàn, thề trung thành với giáo luật của Imperator, hoặc chuyên cần tuân theo giáo lý, số phận lầm lạc của chúng sẽ được điều chỉnh bởi những cánh buồm của Người Hành Hương.
Chúng ta sẽ cầu nguyện cho chúng ngày đêm, để chúng được cứu rỗi bởi Sentinel Imperator vĩ đại của chúng ta. Ngợi ca Imperator.

<i>Mạng Lưới Gián Điệp của Giáo Đoàn Vực Sâu</i>
À, người bạn của ta, người đồng hành trên hành trình tìm kiếm tự do và chân lý này, ta van nài ngươi—hãy mở tập truyền đơn này ở nơi an toàn, tránh xa những ánh mắt tò mò. Điều ta sắp tiết lộ là tối quan trọng cho sự an toàn của ngươi. Hãy học cách nhận diện gián điệp của Giáo Đoàn Vực Sâu và tránh khỏi nanh vuốt của chúng.
Tất cả Echoes mang vầng hào quang vàng trên đầu đều là gián điệp của Giáo Đoàn Vực Sâu, phục vụ với tư cách "Thiên Sứ". Chúng luôn xuất hiện bên cạnh các Acolyte, đóng vai tay sai của Giáo Đoàn để tiêu diệt những kẻ dị giáo. Rinascita, Vùng Đất Echo ư? Ha... ngay cả những lời châm biếm sắc bén nhất cũng không thể lột tả hết sự phi lý của thực tại mà chúng ta đang gánh chịu.
Đầu tiên, ngươi phải cảnh giác với những Echoes đèn lồng, gọi là Lucerna. Dù trông có vẻ vô hại, chúng có khả năng phát hiện những kẻ dị giáo ẩn nấp trong bóng tối đêm đen. Ánh sáng của chúng có thể soi đường, nhưng cũng là vũ khí chói lòa, khiến người ta mất phương hướng. Đã từng có trường hợp ai đó dùng khả năng Echoes của Fae Ignis để ẩn thân, nhưng vẫn bị lộ dưới ánh sáng không thương tiếc của Lucerna.
Tiếp theo, có những bức tượng thạch cao thường thấy nhất, nổi tiếng với cái tên La Guardia, những kẻ bảo vệ trung thành nhất của Giáo Đoàn. Nếu không có lệnh từ các Acolyte, chúng đứng bất động như tượng đá. Tuy nhiên, nếu ngươi bị La Guardia truy đuổi, đừng phí thời gian chiến đấu với chúng. Thay vào đó, hãy tập trung tìm kiếm Acolyte của Order Penitentiary đang ra lệnh.
Trong số tất cả những tay sai này, đáng ghét nhất là Vox Sanctus, đậu trên nóc các tòa nhà nhà thờ. Chúng đóng vai lính danh dự của Giáo Đoàn. Dù không thể di chuyển tự do, chúng dùng nhạc cụ để rao giảng những giáo lý giả dối ngày đêm. Những bài thuyết giáo ấy thấm vào tâm hồn người Ragunnesi, đầu độc tư tưởng của họ.
Ngươi có thể tưởng tượng được không, những đứa trẻ Ragunna bị buộc phải nghe những lời rao giảng vô nghĩa ngay từ khi mới chào đời? Áp bức bằng vũ lực có thể còn chừa chỗ cho sự phản kháng, nhưng ở Ragunna, làm sao thoát khỏi những xiềng xích tinh thần lenỏi vào mọi ngóc ngách của cuộc sống?

Đơn Khiếu Nại về Dị Giáo
Kính gửi Ngài Acolyte,

Tôi, Charles Tornatore, xin báo cáo một hành vi dị giáo—một đoàn kịch ngầm có tên Panacea đã dám diễn lại vở kịch bị cấm <i>Những Người Ragunnesi Bay</i>, thêm vào vô số ẩn dụ độc hại và hình ảnh báng bổ. Tôi đã ghi lại những dòng sau đây theo trí nhớ:
<i>"Lời của Primus như những câu thần chú muối chua. Ngay cả Gondola cũng phải tê tái khi nghe thấy."</i>
—Trích Cảnh I, Hồi 1
<i>Liệu chiếc bánh mì cán bột trong tay ta có đủ cứng để đập tan kẻ thù đức tin của chúng ta không?</i>
—Trích Cảnh I, Hồi 3 (Ghi chú: Dòng này, do một Acolyte nói ra, đã hạ thấp thánh vật của Giáo Đoàn, gọi nó chỉ là một mẩu bánh mì.)
<i>Nhân danh Imperator trên cao, xin chứng giám cho tình yêu của chúng con, đẹp đẽ như ánh bình minh.</i>
—Trích Cảnh II, Hồi 1 (Ghi chú: Dòng này đánh dấu cảnh bỏ trốn của nam nữ chính.)
...
Tôi rất tiếc vì không thể nhớ hết những lời báng bổ trong vở kịch. Sao chúng dám báng bổ đức tin cao quý của chúng ta như vậy?
Dù chúng đeo mặt nạ trong suốt buổi diễn, tôi vẫn nhận ra chúng qua dáng vẻ và giọng nói. Không ngạc nhiên khi chúng phục vụ gia tộc Montelli (Danh sách tên chi tiết được đính kèm).
Ngợi ca Imperator.""",
    
    "LORE_0007442": "Jinzhou, thành trì trấn giữ biên giới Huanglong, đồng thời là cửa ngõ đầu tiên của vùng đất này đối với những ai đến từ hải ngoại. Dãy Núi Linh Hồn trải dài từ bắc xuống nam, chia Huanglong thành hai miền: Nội Huanglong với sáu thành phố, và Ngoại Huanglong, nơi Jinzhou kiên cường đứng vững. Những ngọn núi này tạo thành bức tường thiên nhiên, với những hẻm núi là lối vào duy nhất dẫn vào Nội Huanglong, được canh giữ ngày đêm bởi đội Midnight Rangers của Jinzhou.\n\nViệc xây dựng pháo đài đầu tiên ở Ngoại Huanglong bắt đầu từ khi Tacet Field Norfall Barrens xuất hiện, nơi các đợt bùng phát Tacet Discord bắt đầu tàn phá khu vực. Sau nhiều tháng chiến đấu khốc liệt, quân đội không còn chịu nổi sức tấn công của các đợt bùng phát và buộc phải rút lui về Gorges of Spirits để tử thủ. Những chiến binh đã kiên cường chiến đấu suốt nhiều ngày, khi phòng tuyến liên tục bị phá vỡ rồi giành lại. Trong thời gian đó, Hiện tượng Waveworn trên khắp Huanglong dường như đang trong giai đoạn hoạt động mạnh, và có vẻ như các Tacet Discord được dẫn dắt bởi một thủ lĩnh bí ẩn, nhằm hội tụ về Nội Huanglong.\n\nVào thời khắc quyết định, quân tiếp viện từ sáu thành phố đã được điều đến Gorges of Spirits, nơi các chiến binh biên giới vẫn chiến đấu với ý chí bất khuất. Khi trận chiến lên đến đỉnh điểm, sự xuất hiện của kẻ Vô Vương đã phá vỡ thế bế tắc. Bất cứ nơi nào hắn xuất hiện, bóng tối bao trùm bầu trời, và một bầu không khí ngột ngạt bao trùm, khiến các chiến binh nghẹt thở. Dù vậy, họ vẫn kiên cường giữ vững phòng tuyến, sẵn sàng hy sinh để kéo dài thời gian phá hủy lối vào Gorges of Spirits, ngăn chặn đợt bùng phát Tacet Discord. Họ làm điều đó với ý thức rằng phần lớn trong số họ sẽ bị mắc kẹt ở Ngoại Huanglong cùng với lũ Tacet Discord mãi mãi.\n\nTrong khoảnh khắc sinh tử đó, tiếng gầm vang dội của một con Loong hùng mạnh vang lên từ sâu thẳm Gorges of Spirits, như sấm truyền khắp đại địa. Tiếng gầm ấy vang dội từ hẻm núi, đẩy lùi đội quân Tacet Discord đang chuẩn bị tràn vào. Trong nháy mắt, một con Loong bay vút trên bầu trời, xua tan mây đen và mang ánh sáng trở lại. Rồi một nhân vật kỳ lạ với đôi mắt vàng xuất hiện, đứng giữa lũ Tacet Discord và các chiến binh, đối đầu với kẻ Vô Vương trong một cuộc giằng co quyết liệt. Như trong thơ có câu: \"Giáp phục lấp lánh vảy Loong vàng dưới ánh dương.\" Khi quân tiếp viện từ sáu thành phố đến, liên quân đã đẩy lùi đợt bùng phát Tacet Discord và kẻ Vô Vương về phía bắc Trung Nguyên.\n\nSau trận chiến này, Ngoại Huanglong đã hồi sinh từ đống tro tàn. Sự xuất hiện của cả Threnodian lẫn sinh vật thần thánh báo hiệu nhu cầu xây dựng một thành phố mới để trở thành pháo đài biên giới của Huanglong. Lấy cảm hứng từ âm \"Jin\" trong \"Guan Jin\" (nghĩa là \"ải quan\"), và hình dáng của chữ \"Jin\" tượng trưng cho tiếng gầm của Loong, thành phố này được đặt tên là Jinzhou.",
    
    "LORE_0007650": "Angry Listener: Đồ thoái hóa! Đồ đạo đức giả kiêu ngạo, tất cả bọn ngươi! Mấy người có biết chuyện gì đã xảy ra không... chẳng biết gì cả!\nAngry Listener: Liệu Hội đã biến những hy sinh của chúng ta thành những câu chuyện kể bên tách trà sao? Phước lành của Sentinel. Thật nực cười!\nAngry Listener: Các người đã ở đâu khi chúng ta chiến đấu với lũ Tacet Discord tại Whisperwind Haven? Các người đã ở đâu? Sentinel đã ở đâu?!\nAngry Listener: Chúng ta không chiến đấu vì Sentinel hay cái Giáo Đoàn chết tiệt ấy. Chúng ta chiến đấu vì chính mình! Đồ đạo đức giả!",
    
    "LORE_0008542": "Lần đầu tiên Hiyuki nghe được sự thật về quá khứ của chính mình, nó lại tuôn ra từ đôi môi say khướt của Gyokuro. Hiyuki mím chặt môi. Không nói lời nào, cô tự rót cho mình một ly rượu đắng.\n \n\"Hiyuki. Hiyuki yêu quý của ta...\"\n\"Con không thể làm điều này. Con không thể trở thành Miko chết tiệt của Flaming Sakura... Cuộc đời con không nên như thế này!\"\n \nÁnh mắt Hiyuki sắc lại. Nếu dân làng <te href=851074>Ashinohara</te> thấy vị Miko Flaming Sakura thường ngày đoan trang, đĩnh đạc của họ lại hành xử như thế này sau cánh cửa đóng kín...\n \nKim giây lách cách. Kim phút theo sau. At last, kim giờ cũng nhích lên. Theo giờ Ashinohara, khoảnh khắc này đánh dấu bước trưởng thành của Hiyuki. Cô thở dài rồi nốc cạn ly rượu trong một hơi nóng rát.\n \n\"Ngài làm được. Sao ta lại không?\"\n \nCồn đốt cháy cổ họng, rồi lắng đọng như chì trong thân hình mảnh mai của cô. Vậy ra đây là thứ gọi là \"rượu trưởng thành\". Hiyuki quyết định, hương vị này chẳng đáng để chờ đợi. Cô đứng dậy, phủ tấm chăn lên người Gyokuro đang lẩm bẩm. Cô đứng lặng trong góc phòng một lúc lâu. At last, cô bước tới, giũ chăn cho kín rồi nhẹ nhàng đóng cửa lại.\n \nSáng hôm sau, cơn thịnh nộ của Gyokuro với người quản gia phụ trách lễ kế vị Bùa Di Sản vang xa đến tận hai dãy phố.\n \nSức mạnh của Suzu nằm ở khả năng \"vay mượn tương lai\". Nói đơn giản, mỗi lần sử dụng đều lấy đi một phần tuổi thọ của người mang nó. Trong trường hợp tồi tệ nhất, người kế vị nhận chuông hôm nay có thể tan biến vào hư vô ngay trong trận chiến đầu tiên với Threnodian. Vì cái giá quá đắt đỏ, người kế vị thường được chọn từ sớm. Hiyuki đã ở bên Gyokuro hơn một thập kỷ. Dù Gyokuro không chịu chỉ định cô... thì còn ai khác có thể được chọn?\n \nNgười quản gia, không thể chịu nổi cơn giận của Gyokuro, chỉ biết nở nụ cười gượng gạo, cố làm dịu tình hình. \"Dù không phải Hiyuki, chắc chắn ngài cũng phải chọn một người, Thánh Nữ.\"\n \nGyokuro im lặng trong vài hơi thở. Bà thở dài, hắng giọng, chuẩn bị tiếp tục cơn thịnh nộ.\n \nChính Hiyuki là người mở cửa, chấm dứt trò hề này.\n \n\"Nhiều năm qua, con đã cùng ngài đi khắp Ashinohara. Con biết mỗi nhiệm vụ đòi hỏi gì.\"\n\"Con đã thuần thục mọi kỹ năng một Miko phải có. Từ việc kết bùa, đến các điệu múa nghi lễ—tất cả đều do chính ngài chọn thầy dạy.\"\n\"Chỉ có con mới có thể đảm bảo danh tiếng của Flaming Sakura không bị hoen ố, Gyokuro... Không, Thánh Nữ.\"\n \nGyokuro cau mày. Bà vung tay ra hiệu không cần thiết.\n\n\"Con đã học hết rồi à? Vậy sao con không hiểu Suzu sẽ là cái chết của con?\"\n\"Con chỉ là đứa trẻ mồ côi ngài nhận nuôi. Gia đình con đã nằm dưới tuyết sau cuộc tấn công của Threnodian. Con chẳng còn gì để mất.\"\n \nCăn phòng chìm trong im lặng ngột ngạt. Âm thanh duy nhất là tiếng cọ xát khàn khàn của ngón tay cái Gyokuro khi bà chà xát chiếc chuông trên cổ tay. Bà cố nói gì đó, nhưng cuối cùng, chẳng lời nào thốt ra.",
    
    "LORE_0008554": "<te href=851074>Ashinohara</te> vẫn chiếm trọn tâm trí tôi... nhưng tôi không gọi đó là gánh nặng. Quá khứ đã an bài. Điều còn lại là xử lý những gì đã bỏ lại. Dù không còn xuất hiện trên bất kỳ bản đồ nào, vùng đất ấy vẫn mang trong mình di sản được tạo ra để trường tồn.",
    
    "NAME_TITLE_0020433": "Chế độ bảo vệ mắt",
    "NAME_TITLE_0032743": "Chế độ bảo vệ mắt",
    "UI_0006542": "Chế độ bảo vệ mắt",
    
    "NAME_TITLE_0024051": "Nhưng thật tiếc khi tôi không thể tham dự lễ tiễn biệt Professor Edgar…",
    "NAME_TITLE_0031619": "Quà tặng Đại đoàn viên",
    
    "SKILL_DESCRIPTION_0004592": "Tiêu hao STA và vào trạng thái Rocksteady Defense. Thả nút Heavy Attack để kết thúc Rocksteady Defense và lập tức tung đòn tấn công, gây Havoc DMG.",
    
    "SKILL_DESCRIPTION_0008814": "<size=40><color=Title>Heavy Attack - Imminent Oblivion</color></size>\nCarlotta kích hoạt <color=Highlight>Tinted Crystal</color> mỗi {0} giây.\nKhi Chất Lượng đạt tối đa và <color=Highlight>Tinted Crystal</color> được kích hoạt, giữ <color=Highlight>Normal Attack</color> để tiêu hao toàn bộ Chất Lượng và tung ra Heavy Attack <color=Highlight>Imminent Oblivion</color>, sau đó <color=Highlight>Tinted Crystal</color> sẽ bắt đầu Cooldown.\nGây <color=Ice>Glacio DMG</color> và giảm Cooldown chiêu của Resonance Skill <color=Highlight>Art of Violence</color> đi {1} giây.\n<size=10> </size>\n<size=40><color=Title>Final Bow</color></size>\nKhi Chất Lượng đạt tối đa,vào trạng thái <color=Highlight>Final Bow</color>.\nIncrease Hệ Số Sát Thương của Resonance Liberation <color=Highlight>Era of New Wave</color>, Resonance Liberation <color=Highlight>Death Knell</color> và Resonance Liberation <color=Highlight>Fatal Finale</color> lên {14}. Hiệu ứng này sẽ kết thúc khi Carlotta rời khỏi chiến trường trong <color=Highlight>Twilight Tango</color> hoặc khi <color=Highlight>Twilight Tango</color> kết thúc.\n<size=10> </size>\n<size=40><color=Title>Substance</color></size>\nCarlotta có thể tích lũy tối đa {2} điểm Chất Lượng.\nKhông thể nhận Chất Lượng khi đang trong <color=Highlight>Twilight Tango</color>.\nCó thể nhận Chất Lượng bằng các cách sau: Intro Skill <color=Highlight>Wintertime Aria</color>, tiêu thụ Pha Lê Dẻo Dai qua Resonance Skill <color=Highlight>Chromatic Splendor</color>, Basic Attack <color=Highlight>Necessary Measures</color> và <color=Highlight>Dodge Counter</color>.\n<size=10> </size>\n<size=40><color=Title>Moldable Crystal</color></size>\nCarlotta có thể tích lũy tối đa {6} Pha Lê.\nKhông thể nhận Pha Lê Dẻo Dai khi đang trong <color=Highlight>Twilight Tango</color>.\nCó thể nhận Pha Lê Dẻo Dai bằng các cách sau: <color=Highlight>Intro Skill</color>, <color=Highlight>Basic Attack Stage 2</color>, <color=Highlight>Heavy Attack</color>, Đòn Mid-air Attack <color=Highlight>Customary Greetings</color>, Resonance Skill <color=Highlight>Art of Violence</color> và <color=Highlight>Dodge</color>.",
    
    "SKILL_DESCRIPTION_0008966": "Lupa phóng Ngọn Cờ Wildfire Dã vào mục tiêu, gây <color=Fire>Fusion DMG</color> và hồi {0} điểm <te href=850174>Wolflame</te>. <color=Highlight>Mark</color> mục tiêu trong {1} giây. Sau khi sử dụng Resonance Skill <color=Highlight>Shewolf's Hunt</color>, Lupa có thể thực hiện <color=Highlight>Feral Fang</color> trong một khoảng thời gian nhất định.\nCó thể thực hiện khi đang ở gần mặt đất trên không.\n- Giữ Resonance Skill để bật lên không trung, sau đó {Cus:Ipt,Touch=tap PC=press Gamepad=press} <color=Highlight>Normal Attack</color> đúng lúc để tung <color=Highlight>Mid-air Attack Stage 1</color>.\n\n<size=40><color=Title>Resonance Skill - Feral Fang</color></size>\nLupa khóa mụcaim mục tiêu, gây <color=Fire>Fusion DMG</color> và hồi {2} điểm <te href=850174>Wolflame</te>. Hệ số Sát Thương đối với mục tiêu <color=Highlight>marked</color> tăng {3}. Resonance Skill - Nanh Dã Thú sẽ bắt đầu Cooldown nếu không được kích hoạt kịp thời hoặc khi Lupa bị thay ra.",
    
    "STORY_DIALOGUE_0005890": "{PlayerName}, cậu thật tuyệt vời! Ngay cả câu đố khó như vậy cậu cũng biết đáp án!",
    "STORY_DIALOGUE_0005900": "{PlayerName}, cậu thật tuyệt vời! Ngay cả câu đố khó như vậy cậu cũng biết đáp án!",
    "STORY_DIALOGUE_0005924": "{PlayerName}, cậu thật tuyệt vời! Ngay cả câu đố khó như vậy cậu cũng biết đáp án!",
    "STORY_DIALOGUE_0005935": "{PlayerName}, cậu thật tuyệt vời! Ngay cả câu đố khó như vậy cậu cũng biết đáp án!",
    "STORY_DIALOGUE_0005947": "{PlayerName}, cậu thật tuyệt vời! Ngay cả câu đố khó như vậy cậu cũng biết đáp án!",
    "STORY_DIALOGUE_0005959": "{PlayerName}, cậu thật tuyệt vời! Ngay cả câu đố khó như vậy cậu cũng biết đáp án!",
    
    "STORY_DIALOGUE_0009397": "Chắc cậu cũng không biết giáo phái của mình, hay có biệt danh gì nhỉ? Thảo nào mọi người mới gọi cậu là \"cậu bé\" suốt thôi...",
    
    "STORY_DIALOGUE_0011696": "Khu vực này trên bản đồ đã chuyển sang màu đỏ, {PlayerName}. Số lượng báo cáo từ các tín sứ cũng tăng lên.",
    
    "STORY_DIALOGUE_0018022": "Cậu và Chisa trở lại trung tâm thành phố, đúng nơi cậu lần đầu đặt chân đến Honami City. Những đám mây trên đỉnh Neon Tower đã tan, ánh mặt trời chiếu rọi xuống thành phố như một sự tái sinh. Abby từ trên trời hạ cánh an toàn vào vòng tay cậu.\n\nKhoảnh khắc đó, cả hai đều nhận ra rằng phong ấn của Sonoro đã bị phá vỡ. Các cậu đã mở ra con đường kết nối Honami City với thế giới bên ngoài.",
    
    "STORY_DIALOGUE_0021498": "Tên trộm nhà đó ăn cắp kho báu à? Sao, cậu định nói ta đã thiếu trách nhiệm à?",
    
    "STORY_DIALOGUE_0026861": "Mình nên đặt nó ở đây? Hay ở kia? Hmm… chắc treo ở đằng kia vậy.",
    
    "STORY_DIALOGUE_0031755": "Samousas à? Cậu làm gì ở đây thế? Ta vừa nghe thấy cậu hét lên \"bộ bài\" với \"bậc thầy đối quyết tối thượng\" à? Chuyện gì đang xảy ra vậy?",
    
    "STORY_DIALOGUE_0040090": "Vậy là cậu có thể vào Dark Tide. Thảo nào chúng ta không tìm thấy cậu.",
    
    "STORY_DIALOGUE_0040977": "Dù sao, ưu tiên của chúng ta bây giờ là tập trung lực lượng, giữ vững phòng tuyến và tận dụng thời gian mà cô ấy đang kéo dài cho chúng ta.",
    
    "STORY_DIALOGUE_0041773": "Bọn Giám Sát đã không hoàn thành nhiệm vụ và lừa dối chúng ta…",
    
    "STORY_DIALOGUE_0041928": "Nhiệm vụ của chúng ta là bảo vệ Septimont và người dân nơi đây. Chúng ta sẽ giữ vững ở đây, cho đến khi họ trở về trong vinh quang.",
    
    "STORY_DIALOGUE_0046312": "Nhìn thẳng vào mắt ta và trả lời câu hỏi chết tiệt này đi!",
    
    "STORY_DIALOGUE_0051609": "Ừ, ừ… {PlayerName}, cái này. Nhờ cậu đưa cho Thánh Nữ giùm tôi.",
    
    "STORY_DIALOGUE_0053017": "Tớ vẫn muốn Dhalifa trở về nhà, nhưng vì cô ấy đã quyết định rồi, tớ sẽ tôn trọng điều đó.",
    
    "STORY_DIALOGUE_0065675": "\"Các cậu... học sinh à? Không. Khí tức của Exostrider... mạnh quá.\"",
    "STORY_DIALOGUE_0067378": "\"K-không! Chúng không bắt được tôi đâu! Được rồi... Cậu có khí tức của Exostrider. Tôi sẽ nghe lời cậu.\"",
    
    "STORY_DIALOGUE_0069762": "Mùa này, chủ đề tập trung vào những ý tưởng kinh doanh của các tín sứ dưới tiêu đề \"Đánh giá Vòng Kinh Doanh qua Trải nghiệm Người dùng.\"",
    
    "STORY_DIALOGUE_0090167": "Nghe có chút quen quen... Dù sao, vì Đội Trưởng đã nói, tôi phải nghe theo thôi.",
    
    "STORY_DIALOGUE_0120059": "Đúng như cái tên của nó thôi. Nhưng... đừng tạo ra nó trừ khi sinh tử tồn vong.",
    
    "UI_0009992": "Với Resonance Skill <color=Highlight>Light Tràn</color>, Jinhsi gây <color=Light>Spectro DMG</color> và vào <color=Highlight>Incarnation</color>.",
    "UI_0010297": "Khi Prayer đầy, giữ Resonance Skill để thi triển <color=Highlight>Utter Confession</color> và vào Confession status."
}

def main():
    workspace = Path(r"C:\Users\tduy2\Documents\antigravity\silly-darwin")
    json_dir = workspace / "mistral_translate_work" / "split_by_prompt" / "json"
    out_dir = workspace / "mistral_translate_work" / "split_by_prompt" / "ui_translation_pack"
    
    json_files = glob.glob(str(json_dir / "**" / "*.json"), recursive=True)
    print(f"Found {len(json_files)} JSON files to scan.")
    
    modified_count = 0
    modified_files_count = 0
    
    for f_path in json_files:
        with open(f_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f, strict=False)
            except Exception as e:
                print(f"Error loading {f_path}: {e}")
                continue
        
        file_modified = False
        for row in data:
            sid = row.get("split_id")
            if sid in manual_corrections:
                old_val = row.get("new_translation_vi")
                new_val = manual_corrections[sid]
                if old_val != new_val:
                    row["new_translation_vi"] = new_val
                    row["status"] = "translated"
                    file_modified = True
                    modified_count += 1
                    print(f"[{sid}] Updated translation in {Path(f_path).name}")
        
        if file_modified:
            with open(f_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            modified_files_count += 1
            
    print(f"Corrected {modified_count} records in {modified_files_count} files.")
    
    # Rebuild Excel
    print("Rebuilding consolidated Excel: ui_all.xlsx...")
    ui_json_dir = json_dir / "ui"
    ui_files = glob.glob(str(ui_json_dir / "**" / "*.json"), recursive=True)
    records = []
    for f_path in ui_files:
        with open(f_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f, strict=False)
                if isinstance(data, list):
                    records.extend(data)
                else:
                    records.append(data)
            except Exception as e:
                print(f"Error loading {f_path} for Excel export: {e}")
                
    columns = [
        'split_id', 'prompt_domain', 'prompt_file', 'source_file',
        'original_index', 'database', 'table', 'primary_key_column',
        'primary_key', 'column', 'category', 'source_en',
        'new_translation_vi', 'translator_note'
    ]
    df = pd.DataFrame(records)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    df = df[columns]
    df = df.sort_values(by=['source_file', 'original_index'])
    
    excel_path = out_dir / "ui_all.xlsx"
    df.to_excel(excel_path, index=False)
    print(f"Excel regenerated successfully at {excel_path}!")

if __name__ == "__main__":
    main()
